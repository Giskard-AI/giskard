package ai.giskard.web.rest.controllers;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.User;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.ee.jwt.TokenProvider;
import ai.giskard.service.MailService;
import ai.giskard.service.UserService;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.user.RoleDTO;
import ai.giskard.web.dto.user.UserDTO;
import ai.giskard.web.rest.errors.BadRequestAlertException;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.constraints.Email;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v2")
@Validated
@RequiredArgsConstructor
public class PublicUserController {

    private static final List<String> ALLOWED_ORDERED_PROPERTIES = Collections.unmodifiableList(
        Arrays.asList("id", "login", "firstName", "lastName", "email", "activated", "langKey")
    );

    private final Logger log = LoggerFactory.getLogger(PublicUserController.class);

    private final UserService userService;
    private final UserRepository userRepository;
    private final MailService mailService;
    private final TokenProvider tokenProvider;
    private final ApplicationProperties applicationProperties;

    private final GiskardMapper giskardMapper;

    @GetMapping("/users/coworkers")
    public List<UserDTO> getCoworkers(@AuthenticationPrincipal UserDetails user) {
        log.debug("REST request to get coworkers of {}", user.getUsername());
        return userService.getAllCoworkers(user.getUsername()).stream()
            .map(giskardMapper::userToUserDTO).collect(Collectors.toList());
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
    public void inviteUserSignup(@AuthenticationPrincipal UserDetails currentUserDetails, @RequestParam @Email String email) {
        User currentUser = userService.getUserByLogin(currentUserDetails.getUsername());
        if (currentUser.getEmail().equals(email)) {
            throw new BadRequestAlertException("Cannot invite yourself");
        }
        if (userRepository.findOneByEmailIgnoreCase(email).isPresent()) {
            throw new BadRequestAlertException("This email is already registered");
        }

        String token = tokenProvider.createInvitationToken(currentUser.getEmail(), email);
        String inviteLink = applicationProperties.getMailBaseUrl() + "/auth/signup?token=" + token;

        mailService.sendUserSignupInvitationEmail(currentUser.getEmail(), email, inviteLink);

    }

}
