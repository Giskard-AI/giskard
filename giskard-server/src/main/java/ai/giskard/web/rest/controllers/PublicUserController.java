package ai.giskard.web.rest.controllers;

import ai.giskard.domain.User;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.jwt.TokenProvider;
import ai.giskard.service.MailService;
import ai.giskard.service.UserService;
import ai.giskard.web.dto.user.AdminUserDTO;

import java.util.*;
import java.util.Collections;
import java.util.stream.Collectors;

import ai.giskard.web.dto.user.RoleDTO;
import ai.giskard.web.dto.user.UserDTO;
import ai.giskard.web.rest.errors.BadRequestAlertException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springdoc.api.annotations.ParameterObject;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;
import tech.jhipster.config.JHipsterProperties;
import tech.jhipster.web.util.PaginationUtil;

import javax.validation.constraints.Email;

@RestController
@RequestMapping("/api/v2")
public class PublicUserController {

    private static final List<String> ALLOWED_ORDERED_PROPERTIES = Collections.unmodifiableList(
        Arrays.asList("id", "login", "firstName", "lastName", "email", "activated", "langKey")
    );

    private final Logger log = LoggerFactory.getLogger(PublicUserController.class);

    private final UserService userService;
    private final UserRepository userRepository;
    private final MailService mailService;
    private final TokenProvider tokenProvider;
    private final JHipsterProperties jHipsterProperties;




    public PublicUserController(UserService userService, UserRepository userRepository, MailService mailService, TokenProvider tokenProvider, JHipsterProperties jHipsterProperties) {
        this.userService = userService;
        this.userRepository = userRepository;
        this.mailService = mailService;
        this.tokenProvider = tokenProvider;
        this.jHipsterProperties = jHipsterProperties;
    }

    @GetMapping("/users/coworkers")
    public List<UserDTO> getCoworkers(@AuthenticationPrincipal UserDetails user) {
        log.debug("REST request to get coworkers of {}", user.getUsername());

        return userService.getAllCoworkers(user.getUsername()).stream()
            .map(UserDTO::new).collect(Collectors.toList());
    }

    private boolean onlyContainsAllowedProperties(Pageable pageable) {
        return pageable.getSort().stream().map(Sort.Order::getProperty).allMatch(ALLOWED_ORDERED_PROPERTIES::contains);
    }

    /**
     * Gets a list of all roles.
     *
     * @return a string list of all roles.
     */
    @GetMapping("/roles")
    public List<RoleDTO> getAuthorities() {
        return AuthoritiesConstants.AUTHORITY_NAMES.entrySet().stream()
            .map(auth -> new RoleDTO(auth.getKey(), auth.getValue()))
            .collect(Collectors.toList());
    }

    @PostMapping("/users/invite")
    public void inviteUser(@AuthenticationPrincipal UserDetails currentUserDetails, @Email String email, String projectName) {
        User currentUser = userService.getUserByLogin(currentUserDetails.getUsername());
        if (currentUser.getEmail().equals(email)) {
            throw new BadRequestAlertException("Cannot invite yourself");
        }
        if (userRepository.findOneByEmailIgnoreCase(email).isPresent()) {
            throw new BadRequestAlertException("This email is already registered");
        }

        String token = tokenProvider.createInvitationToken(currentUser.getEmail(), email);
        String inviteLink = jHipsterProperties.getMail().getBaseUrl() + "/auth/signup?token=" + token;

        mailService.sendUserInvitationEmail(currentUser.getEmail(), email, inviteLink, projectName);

    }

}
