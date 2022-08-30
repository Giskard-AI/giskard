package ai.giskard.web.rest.controllers;

import ai.giskard.domain.GeneralSettings;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.GeneralSettingsService;
import ai.giskard.web.dto.config.AppConfigDTO;
import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.dto.user.RoleDTO;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.PropertySource;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.List;

import static ai.giskard.security.AuthoritiesConstants.ADMIN;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/settings")
@PropertySource("${spring.info.build.location:classpath:META-INF/build-info.properties}")
public class SettingsController {
    private final Logger log = LoggerFactory.getLogger(SettingsController.class);
    private final UserRepository userRepository;
    @Value("${build.version}")
    private String buildVersion;
    private final GeneralSettingsService settingsService;


    @PostMapping("")
    @PreAuthorize("hasAuthority(\"" + ADMIN + "\")")
    @Transactional
    public GeneralSettings saveGeneralSettings(@RequestBody GeneralSettings settings) {
        return settingsService.save(settings);
    }

    @GetMapping("")
    @Transactional
    public AppConfigDTO getApplicationSettings(@AuthenticationPrincipal final UserDetails user) {
        log.debug("REST request to get all public User names");
        AdminUserDTO userDTO = userRepository
            .findOneWithRolesByLogin(user.getUsername())
            .map(AdminUserDTO::new)
            .orElseThrow(() -> new RuntimeException("User could not be found"));

        List<RoleDTO> roles = AuthoritiesConstants.AUTHORITY_NAMES.entrySet().stream()
            .map(auth -> new RoleDTO(auth.getKey(), auth.getValue()))
            .toList();

        return AppConfigDTO.builder()
            .app(AppConfigDTO.AppInfoDTO.builder()
                .generalSettings(settingsService.getSettings())
                .version(buildVersion)
                .planCode("open-source")
                .planName("Open Source")
                .roles(roles)
                .build())
            .user(userDTO)
            .build();
    }
}
