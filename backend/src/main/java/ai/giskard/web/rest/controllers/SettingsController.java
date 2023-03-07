package ai.giskard.web.rest.controllers;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.GeneralSettings;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.SecurityUtils;
import ai.giskard.service.GeneralSettingsService;
import ai.giskard.service.ee.FeatureFlagService;
import ai.giskard.service.ml.MLWorkerSecretKey;
import ai.giskard.service.ml.MLWorkerSecurityService;
import ai.giskard.web.dto.config.AppConfigDTO;
import ai.giskard.web.dto.config.MLWorkerConnectionInfoDTO;
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

import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;

import static ai.giskard.security.AuthoritiesConstants.ADMIN;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/settings")
@PropertySource(value = "${spring.info.build.location:classpath:META-INF/build-info.properties}", ignoreResourceNotFound = true)
@PropertySource(value = "${spring.info.build.location:classpath:git.properties}", ignoreResourceNotFound = true)
public class SettingsController {
    private final Logger log = LoggerFactory.getLogger(SettingsController.class);
    private final UserRepository userRepository;
    @Value("${build.version:-}")
    private String buildVersion;
    @Value("${git.branch:-}")
    private String gitBuildBranch;
    @Value("${git.commit.id.abbrev:-}")
    private String gitBuildCommitId;
    @Value("${git.commit.time:-}")
    private String gitCommitTime;
    private final GeneralSettingsService settingsService;
    private final ApplicationProperties applicationProperties;

    private final MLWorkerSecurityService mlWorkerSecurityService;

    private final FeatureFlagService featureFlagService;


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

        Instant buildCommitTime = null;
        try {
            buildCommitTime = OffsetDateTime.parse(gitCommitTime, DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ssZ")).toInstant();
        } catch (Exception e) {
            log.warn("Failed to parse gitCommitTime {}", gitCommitTime);
        }

        return AppConfigDTO.builder()
            .app(AppConfigDTO.AppInfoDTO.builder()
                .generalSettings(settingsService.getSettings())
                .version(buildVersion)
                .buildBranch(gitBuildBranch)
                .buildCommitId(gitBuildCommitId)
                .buildCommitTime(buildCommitTime)
                .planCode("open-source")
                .planName("Open Source")
                .externalMlWorkerEntrypointPort(applicationProperties.getExternalMlWorkerEntrypointPort())
                .externalMlWorkerEntrypointHost(applicationProperties.getExternalMlWorkerEntrypointHost())
                .roles(roles)
                .build())
            .user(userDTO)
            .build();
    }

    @GetMapping("/ml-worker-connect")
    public MLWorkerConnectionInfoDTO getMLWorkerConnectionInfo() throws NoSuchAlgorithmException {
        MLWorkerSecretKey key = mlWorkerSecurityService.registerVacantKey(SecurityUtils.getCurrentAuthenticatedUserLogin());

        return MLWorkerConnectionInfoDTO.builder()
            .externalMlWorkerEntrypointHost(applicationProperties.getExternalMlWorkerEntrypointHost())
            .externalMlWorkerEntrypointPort(applicationProperties.getExternalMlWorkerEntrypointPort())
            .encryptionKey(key.toBase64())
            .keyId(key.getKeyId())
            .build();
    }

    @GetMapping("/featureFlags")
    public Map<FeatureFlagService.FeatureFlag, Boolean> getFeatureFlags() {
        return featureFlagService.getAllFeatures();
    }


}
