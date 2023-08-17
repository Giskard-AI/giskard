package ai.giskard.service;

import ai.giskard.domain.Role;
import ai.giskard.domain.User;
import ai.giskard.repository.RoleRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.dto.user.UserDTO;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.RandomStringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Service class for managing users.
 */
@Service
@RequiredArgsConstructor
public class UserService {

    private final Logger log = LoggerFactory.getLogger(UserService.class);

    private final UserRepository userRepository;

    private final PasswordEncoder passwordEncoder;

    private final RoleRepository roleRepository;

    private final GiskardMapper giskardMapper;

    public Optional<User> activateRegistration(String key) {
        log.debug("Activating user for activation key {}", key);
        return userRepository
            .findOneByActivationKey(key)
            .map(user -> {
                // activate given user for the registration key.
                user.setActivated(true);
                user.setActivationKey(null);
                log.debug("Activated user: {}", user);
                return user;
            });
    }

    public Optional<User> completePasswordReset(String newPassword, String key) {
        log.debug("Reset user password for reset key {}", key);
        return userRepository
            .findOneByResetKey(key)
            .filter(user -> user.getResetDate().isAfter(Instant.now().minus(1, ChronoUnit.DAYS)))
            .map(user -> {
                user.setPassword(passwordEncoder.encode(newPassword));
                user.setResetKey(null);
                user.setResetDate(null);
                return user;
            });
    }

    public Optional<User> requestPasswordReset(String mail) {
        return userRepository
            .findOneByEmailIgnoreCase(mail)
            .filter(User::isActivated)
            .map(user -> {
                user.setResetKey(RandomStringUtils.randomAlphanumeric(20));
                user.setResetDate(Instant.now());
                return user;
            });
    }

    public User registerUser(AdminUserDTO userDTO, String password) {
        userRepository
            .findOneByLogin(userDTO.getLogin().toLowerCase())
            .ifPresent(existingUser -> {
                boolean removed = removeNonActivatedUser(existingUser);
                if (!removed) {
                    throw new UsernameAlreadyUsedException();
                }
            });
        userRepository
            .findOneByEmailIgnoreCase(userDTO.getEmail())
            .ifPresent(existingUser -> {
                boolean removed = removeNonActivatedUser(existingUser);
                if (!removed) {
                    throw new EmailAlreadyUsedException();
                }
            });
        User newUser = new User();
        String encryptedPassword = passwordEncoder.encode(password);
        newUser.setLogin(userDTO.getLogin().toLowerCase());
        // new user gets initially a generated password
        newUser.setPassword(encryptedPassword);
        if (userDTO.getEmail() != null) {
            newUser.setEmail(userDTO.getEmail().toLowerCase());
        }
        newUser.setActivated(true);
        newUser.setEnabled(true);
        // new user gets registration key
        Set<Role> authorities = new HashSet<>();
        roleRepository.findByName(AuthoritiesConstants.AICREATOR).ifPresent(authorities::add);
        newUser.setRoles(authorities);
        userRepository.save(newUser);
        log.debug("Created Information for User: {}", newUser);
        return newUser;
    }

    private boolean removeNonActivatedUser(User existingUser) {
        if (existingUser.isActivated()) {
            return false;
        }
        userRepository.delete(existingUser);
        userRepository.flush();
        return true;
    }

    public User createUser(AdminUserDTO.AdminUserDTOWithPassword userDTO) {
        User user = new User();
        user.setLogin(userDTO.getLogin().toLowerCase());
        user.setDisplayName(userDTO.getDisplayName());
        if (userDTO.getEmail() != null) {
            user.setEmail(userDTO.getEmail().toLowerCase());
        }
        String encryptedPassword = passwordEncoder.encode(userDTO.getPassword());
        user.setPassword(encryptedPassword);
        user.setResetKey(RandomStringUtils.randomAlphanumeric(20));
        user.setResetDate(Instant.now());
        user.setActivated(true);
        user.setEnabled(true);
        if (userDTO.getRoles() != null) {
            Set<Role> roles = userDTO
                .getRoles()
                .stream()
                .map(roleRepository::findByName)
                .filter(Optional::isPresent)
                .map(Optional::get)
                .collect(Collectors.toSet());
            user.setRoles(roles);
        }
        userRepository.save(user);
        log.debug("Created Information for User: {}", user);
        return user;
    }

    /**
     * Update all information for a specific user, and return the modified user.
     *
     * @param userDTO user to update.
     * @return updated user.
     */
    public Optional<AdminUserDTO> updateUser(AdminUserDTO.AdminUserDTOWithPassword userDTO) {
        return Optional
            .of(userRepository.findOneWithRolesById(userDTO.getId()))
            .filter(Optional::isPresent)
            .map(Optional::get)
            .map(user -> {
                user.setLogin(userDTO.getLogin().toLowerCase());
                user.setDisplayName(userDTO.getDisplayName());
                if (userDTO.getEmail() != null) {
                    user.setEmail(userDTO.getEmail().toLowerCase());
                }
                if (userDTO.getPassword() != null) {
                    user.setPassword(passwordEncoder.encode(userDTO.getPassword()));
                }
                Set<Role> managedAuthorities = user.getRoles();
                managedAuthorities.clear();
                userDTO
                    .getRoles()
                    .stream()
                    .map(roleRepository::findByName)
                    .filter(Optional::isPresent)
                    .map(Optional::get)
                    .forEach(managedAuthorities::add);
                User savedUser = userRepository.save(user);
                log.debug("Changed Information for User: {}", savedUser);
                return savedUser;
            })
            .map(AdminUserDTO::new);
    }

    /**
     * Update basic information (first name, last name, email, language) for the current user.
     *
     * @param email       user email address
     * @param displayName display name of a user
     * @param password    user's new password
     * @return
     */
    public Optional<User> updateUser(String login, String email, String displayName, String password) {
        Optional<User> user = userRepository.findOneWithRolesByLogin(login)
            .map(u -> {
                if (displayName != null) {
                    u.setDisplayName(displayName);
                }
                if (email != null) {
                    u.setEmail(email.toLowerCase());
                }
                if (password != null) {
                    u.setPassword(passwordEncoder.encode(password));
                }
                log.debug("Changed Information for User: {}", u);
                return u;
            });
        return user.map(userRepository::saveAndFlush);
    }

    public Page<AdminUserDTO> getAllManagedUsers(Pageable pageable) {
        return userRepository.findAll(pageable).map(AdminUserDTO::new);
    }

    public List<User> getAllCoworkers(String currentUserLogin) {
        return new ArrayList<>(userRepository.getAllWithRolesByLoginNot(currentUserLogin));
    }

    public Page<UserDTO> getAllPublicUsers(Pageable pageable) {
        return userRepository.findAllByIdNotNullAndActivatedIsTrue(pageable).map(giskardMapper::userToUserDTO);
    }

    public Optional<User> getUserWithAuthoritiesByLogin(String login) {
        return userRepository.findOneWithRolesByLogin(login);
    }

    public User getUserByLogin(String login) {
        return userRepository.getOneByLogin(login);
    }


    /**
     * Gets a list of all the authorities.
     *
     * @return a list of all the authorities.
     */
    public List<String> getAuthorities() {
        return roleRepository.findAll().stream().map(Role::getName).toList();
    }
}
