package ai.giskard.web.rest.controllers;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.GeneralSettings;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.GeneralSettingsService;
import ai.giskard.service.ee.FeatureFlagService;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.config.AppConfigDTO;
import ai.giskard.web.dto.config.MLWorkerInfoDTO;
import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.dto.user.RoleDTO;
import ai.giskard.worker.MLWorkerInfo;
import ai.giskard.worker.MLWorkerInfoRequest;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.protobuf.InvalidProtocolBufferException;
import com.google.protobuf.util.JsonFormat;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.PropertySource;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;

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

    @Autowired
    private final MLWorkerService mlWorkerService;

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
                .features(featureFlagService.getAllFeatures())
                .externalMlWorkerEntrypointPort(applicationProperties.getExternalMlWorkerEntrypointPort())
                .roles(roles)
                .build())
            .user(userDTO)
            .build();
    }

    @GetMapping("/ml-worker-info")
    public List<MLWorkerInfoDTO> getMLWorkerInfo() throws JsonProcessingException, InvalidProtocolBufferException, ExecutionException, InterruptedException {
        try (MLWorkerClient internalClient = mlWorkerService.createClient(true, false);
             MLWorkerClient externalClient = mlWorkerService.createClient(false, false)) {
            List<ListenableFuture<MLWorkerInfo>> awaitableResults = new ArrayList<>();

            if (internalClient != null) {
                awaitableResults.add(internalClient.getFutureStub().getInfo(MLWorkerInfoRequest.newBuilder().setListPackages(true).build()));
            }
            if (externalClient != null) {
                awaitableResults.add(externalClient.getFutureStub().getInfo(MLWorkerInfoRequest.newBuilder().setListPackages(true).build()));
            }

            List<MLWorkerInfo> mlWorkerInfos = Futures.successfulAsList(awaitableResults).get();
            List<MLWorkerInfoDTO> res = new ArrayList<>();
            for (MLWorkerInfo info : mlWorkerInfos) {
                if (info != null) {
                    res.add(new ObjectMapper().readValue(JsonFormat.printer().print(info), MLWorkerInfoDTO.class));
                }
            }

            return res;
        }
    }
}
