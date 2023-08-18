package ai.giskard.web.rest.controllers;

import ai.giskard.config.Constants;
import ai.giskard.domain.User;
import ai.giskard.repository.UserRepository;
import ai.giskard.service.GiskardRuntimeException;
import ai.giskard.service.MailService;
import ai.giskard.service.UserDeletionService;
import ai.giskard.service.UserService;
import ai.giskard.service.ee.LicenseService;
import ai.giskard.utils.LicenseUtils;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.rest.errors.BadRequestAlertException;
import ai.giskard.web.rest.errors.EmailAlreadyUsedException;
import ai.giskard.web.rest.errors.LoginAlreadyUsedException;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;
import java.util.List;
import java.util.Optional;

import static ai.giskard.security.AuthoritiesConstants.ADMIN;

/**
 * REST controller for managing users.
 * <p>
 * This class accesses the {@link User} entity, and needs to fetch its collection of authorities.
 * <p>
 * For a normal use-case, it would be better to have an eager relationship between User and Authority,
 * and send everything to the client side: there would be no View Model and DTO, a lot less code, and an outer-join
 * which would be good for performance.
 * <p>
 * We use a View Model and a DTO for 3 reasons:
 * <ul>
 * <li>We want to keep a lazy association between the user and the authorities, because people will
 * quite often do relationships with the user, and we don't want them to get the authorities all
 * the time for nothing (for performance reasons). This is the #1 goal: we should not impact our users'
 * application because of this use-case.</li>
 * <li> Not having an outer join causes n+1 requests to the database. This is not a real issue as
 * we have by default a second-level cache. This means on the first HTTP call we do the n+1 requests,
 * but then all authorities come from the cache, so in fact it's much better than doing an outer join
 * (which will get lots of data from the database, for each HTTP call).</li>
 * <li> As this manages users, for security reasons, we'd rather have a DTO layer.</li>
 * </ul>
 * <p>
 * Another option would be to have a specific JPA entity graph to handle this case.
 */
@RestController
@RequestMapping("/api/v2/admin/users")
@RequiredArgsConstructor
public class UserAdminController {
    private static final List<String> ALLOWED_ORDERED_PROPERTIES = List.of(
        "id",
        "login",
        "firstName",
        "lastName",
        "email",
        "activated",
        "langKey",
        "createdBy",
        "createdDate",
        "lastModifiedBy",
        "lastModifiedDate");

    private final Logger log = LoggerFactory.getLogger(UserAdminController.class);

    private final UserService userService;

    private final UserDeletionService userDeletionService;

    private final UserRepository userRepository;

    private final MailService mailService;
    private final LicenseService licenseService;
    private final GiskardMapper giskardMapper;


    /**
     * {@code POST  /admin/users}  : Creates a new user.
     * <p>
     * Creates a new user if the login and email are not already used, and sends an
     * mail with an activation link.
     * The user needs to be activated on creation.
     *
     * @param userDTO the user to create.
     * @return the {@link ResponseEntity} with status {@code 201 (Created)} and with body the new user, or with status {@code 400 (Bad Request)} if the login or email is already in use.
     */
    @PostMapping("")
    @PreAuthorize("hasAuthority(\"" + ADMIN + "\")")
    public ResponseEntity<AdminUserDTO> createUser(@Valid @RequestBody AdminUserDTO.AdminUserDTOWithPassword userDTO) {
        log.debug("REST request to save User : {}", userDTO);

        if (userDTO.getId() != null) {
            throw new BadRequestAlertException("A new user cannot already have an ID", "userManagement", "idexists");
            // Lowercase the user login before comparing with database
        } else if (userRepository.findOneByLogin(userDTO.getLogin().toLowerCase()).isPresent()) {
            throw new LoginAlreadyUsedException();
        } else if (userRepository.findOneByEmailIgnoreCase(userDTO.getEmail()).isPresent()) {
            throw new EmailAlreadyUsedException();
        } else if (LicenseUtils.isLimitReached(licenseService.getCurrentLicense().getUserLimit(), (int) userRepository.count())) {
            throw new GiskardRuntimeException("User limit is reached. You can upgrade your plan to create more.");
        } else {
            User newUser = userService.createUser(userDTO);
            mailService.sendCreationEmail(newUser);
            return new ResponseEntity<>(giskardMapper.userToAdminUserDTO(newUser), HttpStatus.CREATED);
        }
    }

    /**
     * {@code PUT /admin/users} : Updates an existing User.
     */
    @PutMapping("")
    @PreAuthorize("hasAuthority(\"" + ADMIN + "\")")
    public ResponseEntity<AdminUserDTO> updateUser(@Valid @RequestBody AdminUserDTO.AdminUserDTOWithPassword userDTO) {
        log.debug("REST request to update User : {}", userDTO);
        Optional<User> existingUser = userRepository.findOneByEmailIgnoreCase(userDTO.getEmail());
        if (existingUser.isPresent() && (!existingUser.get().getId().equals(userDTO.getId()))) {
            throw new EmailAlreadyUsedException();
        }
        existingUser = userRepository.findOneByLogin(userDTO.getLogin().toLowerCase());
        if (existingUser.isPresent() && (!existingUser.get().getId().equals(userDTO.getId()))) {
            throw new LoginAlreadyUsedException();
        }
        return userService.updateUser(userDTO)
            .map(response -> ResponseEntity.ok().body(response))
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    }

    /**
     * {@code GET /admin/users} : get all users with all the details - calling this are only allowed for the administrators.
     *
     * @param pageable the pagination information.
     * @return the {@link ResponseEntity} with status {@code 200 (OK)} and with body all users.
     */
    @GetMapping("")
    @PreAuthorize("hasAuthority(\"" + ADMIN + "\")")
    public ResponseEntity<List<AdminUserDTO>> getAllUsers(@org.springdoc.api.annotations.ParameterObject Pageable pageable) {
        log.debug("REST request to get all User for an admin");
        if (!onlyContainsAllowedProperties(pageable)) {
            return ResponseEntity.badRequest().build();
        }

        final Page<AdminUserDTO> page = userService.getAllManagedUsers(pageable);
        return new ResponseEntity<>(page.getContent(), HttpStatus.OK);
    }

    private boolean onlyContainsAllowedProperties(Pageable pageable) {
        return pageable.getSort().stream().map(Sort.Order::getProperty).allMatch(ALLOWED_ORDERED_PROPERTIES::contains);
    }

    /**
     * {@code GET /admin/users/:login} : get the "login" user.
     *
     * @param login the login of the user to find.
     * @return the {@link ResponseEntity} with status {@code 200 (OK)} and with body the "login" user, or with status {@code 404 (Not Found)}.
     */
    @GetMapping("/{login}")
    @PreAuthorize("hasAuthority(\"" + ADMIN + "\")")
    public ResponseEntity<AdminUserDTO> getUser(@PathVariable @Pattern(regexp = Constants.LOGIN_REGEX) String login) {
        log.debug("REST request to get User : {}", login);
        return userService.getUserWithAuthoritiesByLogin(login).map(AdminUserDTO::new)
            .map(response -> ResponseEntity.ok().body(response))
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    }

    /**
     * {@code DELETE /admin/users/:login} : delete the "login" User.
     *
     * @param login the login of the user to delete.
     */
    @DeleteMapping("/{login}")
    @PreAuthorize("hasAuthority(\"" + ADMIN + "\")")
    public ResponseEntity<Void> deleteUser(@PathVariable @Pattern(regexp = Constants.LOGIN_REGEX) String login) {
        log.debug("REST request to delete User: {}", login);
        userDeletionService.deleteUser(login);
        return ResponseEntity.noContent().build();
    }

    /**
     * {@code PATCH /admin/users/:login/disable} : disable the "login" User.
     *
     * @param login the login of the user to disable.
     */
    @PatchMapping("/{login}/disable")
    @PreAuthorize("hasAuthority(\"" + ADMIN + "\")")
    public ResponseEntity<Void> disableUser(@PathVariable @Pattern(regexp = Constants.LOGIN_REGEX) String login) {
        log.debug("REST request to disable User: {}", login);
        userDeletionService.disableUser(login);
        return ResponseEntity.noContent().build();
    }

    /**
     * {@code PATCH /admin/users/:login/enable} : restore the "login" User.
     *
     * @param login the login of the user to be restored.
     */
    @PatchMapping("/{login}/enable")
    @PreAuthorize("hasAuthority(\"" + ADMIN + "\")")
    public ResponseEntity<Void> enableUser(@PathVariable @Pattern(regexp = Constants.LOGIN_REGEX) String login) {
        log.debug("REST request to restore User: {}", login);
        userDeletionService.enableUser(login);
        return ResponseEntity.noContent().build();
    }
}
