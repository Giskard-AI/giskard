package ai.giskard.web.rest.controllers;

import ai.giskard.domain.User;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.SecurityUtils;
import ai.giskard.security.jwt.JWTTokenType;
import ai.giskard.security.jwt.TokenProvider;
import ai.giskard.service.MailService;
import ai.giskard.service.UserService;
import ai.giskard.web.dto.PasswordResetRequest;
import ai.giskard.web.dto.config.AppConfigDTO;
import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.dto.user.RoleDTO;
import ai.giskard.web.dto.user.UpdateMeDTO;
import ai.giskard.web.rest.errors.EmailAlreadyUsedException;
import ai.giskard.web.rest.errors.InvalidPasswordException;
import ai.giskard.web.rest.errors.LoginAlreadyUsedException;
import ai.giskard.web.rest.vm.ManagedUserVM;
import ai.giskard.web.rest.vm.TokenAndPasswordVM;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;
import tech.jhipster.config.JHipsterProperties;

import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

import static ai.giskard.security.AuthoritiesConstants.ADMIN;

/**
 * REST controller for managing the current user's account.
 */
@RestController
@RequestMapping("/api/v2")
public class AccountController {

    public static class AccountResourceException extends RuntimeException {

        public AccountResourceException(String message) {
            super(message);
        }
    }

    private final Logger log = LoggerFactory.getLogger(AccountController.class);

    private final UserRepository userRepository;

    private final UserService userService;

    private final MailService mailService;

    private final TokenProvider tokenProvider;

    private final JHipsterProperties jHipsterProperties;

    public AccountController(UserRepository userRepository, UserService userService, MailService mailService, TokenProvider tokenProvider, JHipsterProperties jHipsterProperties) {
        this.userRepository = userRepository;
        this.userService = userService;
        this.mailService = mailService;

        this.tokenProvider = tokenProvider;
        this.jHipsterProperties = jHipsterProperties;
    }


    @GetMapping("/signuplink")
    @PreAuthorize("hasAuthority(\"" + ADMIN + "\")")
    public String getSignupLink(@AuthenticationPrincipal UserDetails user) {

        String token = tokenProvider.createInvitationToken(userRepository.getOneByLogin(user.getUsername()).getEmail(), null);
        return jHipsterProperties.getMail().getBaseUrl() + "/auth/signup?token=" + token;
    }

    /**
     * {@code POST  /register} : register the user.
     *
     * @param managedUserVM the managed user View Model.
     * @return
     * @throws InvalidPasswordException  {@code 400 (Bad Request)} if the password is incorrect.
     * @throws EmailAlreadyUsedException {@code 400 (Bad Request)} if the email is already used.
     * @throws LoginAlreadyUsedException {@code 400 (Bad Request)} if the login is already used.
     */
    @PostMapping("/register")
    public ResponseEntity<Void> registerAccount(@Valid @RequestBody ManagedUserVM managedUserVM) {
        if (isPasswordLengthInvalid(managedUserVM.getPassword())) {
            throw new InvalidPasswordException();
        }
        if (!tokenProvider.validateToken(managedUserVM.getToken(), JWTTokenType.INVITATION)) {
            return new ResponseEntity<>(HttpStatus.FORBIDDEN);
        }
        userService.registerUser(managedUserVM, managedUserVM.getPassword());
        //mailService.sendActivationEmail(user);
        return new ResponseEntity<>(HttpStatus.CREATED);
    }

    /**
     * {@code GET  /activate} : activate the registered user.
     *
     * @param key the activation key.
     * @throws RuntimeException {@code 500 (Internal Server Error)} if the user couldn't be activated.
     */
    @GetMapping("/activate")
    public void activateAccount(@RequestParam(value = "key") String key) {
        Optional<User> user = userService.activateRegistration(key);
        if (!user.isPresent()) {
            throw new AccountResourceException("No user was found for this activation key");
        }
    }

    /**
     * {@code GET  /authenticate} : check if the user is authenticated, and return its login.
     *
     * @param request the HTTP request.
     * @return the login if the user is authenticated.
     */
    @GetMapping("/authenticate")
    public String isAuthenticated(HttpServletRequest request) {
        log.debug("REST request to check if the current user is authenticated");
        return request.getRemoteUser();
    }

    @GetMapping("/account")
    public AppConfigDTO getApplicationSettings(@AuthenticationPrincipal final UserDetails user) {
        log.debug("REST request to get all public User names");
        AdminUserDTO userDTO = userRepository
            .findOneWithRolesByLogin(user.getUsername())
            .map(AdminUserDTO::new)
            .orElseThrow(() -> new RuntimeException("User could not be found"));

        List<RoleDTO> roles = AuthoritiesConstants.AUTHORITY_NAMES.entrySet().stream()
            .map(auth -> new RoleDTO(auth.getKey(), auth.getValue()))
            .collect(Collectors.toList());
        return new AppConfigDTO(
            new AppConfigDTO.AppInfoDTO("basic", "Basic", 1, roles), userDTO);
    }

    /**
     * {@code POST  /account} : update the current user information.
     *
     * @param userDTO the current user information.
     * @return
     * @throws EmailAlreadyUsedException {@code 400 (Bad Request)} if the email is already used.
     * @throws RuntimeException          {@code 500 (Internal Server Error)} if the user login wasn't found.
     */
    @PutMapping("/account")
    public AdminUserDTO saveAccount(@Valid @RequestBody UpdateMeDTO userDTO) {
        String login = SecurityUtils.getCurrentAuthenticatedUserLogin();
        Optional<User> existingUser = userRepository.findOneByEmailIgnoreCase(userDTO.getEmail());
        if (existingUser.isPresent() && (!existingUser.get().getLogin().equalsIgnoreCase(login))) {
            throw new EmailAlreadyUsedException();
        }
        Optional<User> user = userRepository.findOneByLogin(login);
        if (user.isEmpty()) {
            throw new AccountResourceException("User could not be found");
        }
        Optional<User> updatedUser = userService.updateUser(
            login,
            userDTO.getEmail(),
            userDTO.getDisplayName(),
            userDTO.getPassword()
        );
        return new AdminUserDTO(updatedUser.orElseThrow());
    }

    /**
     * {@code POST   /account/reset-password/init} : Send an email to reset the password of the user.
     *
     * @param request the mail of the user.
     */
    @PostMapping(path = "/account/password-recovery")
    public void requestPasswordReset(@Valid @RequestBody PasswordResetRequest request) {
        Optional<User> user = userService.requestPasswordReset(request.getEmail());
        if (user.isPresent()) {
            mailService.sendPasswordResetMail(user.get());
        } else {
            // Pretend the request has been successful to prevent checking which emails really exist
            // but log that an invalid attempt has been made
            log.warn("Password reset requested for non existing mail");
        }
    }

    /**
     * {@code POST   /account/reset-password/finish} : Finish to reset the password of the user.
     *
     * @param keyAndPassword the generated key and the new password.
     * @throws InvalidPasswordException {@code 400 (Bad Request)} if the password is incorrect.
     * @throws RuntimeException {@code 500 (Internal Server Error)} if the password could not be reset.
     */
    @PostMapping(path = "/account/reset-password")
    public void finishPasswordReset(@RequestBody TokenAndPasswordVM keyAndPassword) {
        if (isPasswordLengthInvalid(keyAndPassword.getNewPassword())) {
            throw new InvalidPasswordException();
        }
        Optional<User> user = userService.completePasswordReset(keyAndPassword.getNewPassword(), keyAndPassword.getToken());

        if (user.isEmpty()) {
            throw new AccountResourceException("No user was found for this reset key");
        }
    }

    private static boolean isPasswordLengthInvalid(String password) {
        return (
            StringUtils.isEmpty(password) ||
            password.length() < ManagedUserVM.PASSWORD_MIN_LENGTH ||
            password.length() > ManagedUserVM.PASSWORD_MAX_LENGTH
        );
    }
}
