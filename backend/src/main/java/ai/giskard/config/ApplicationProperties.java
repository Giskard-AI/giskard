package ai.giskard.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.web.cors.CorsConfiguration;

import java.nio.file.Path;

/**
 * Properties specific to Giskard.
 * <p>
 * Properties are configured in the {@code application.yml} file.
 */
@Setter
@Getter
@ConfigurationProperties(prefix = "giskard", ignoreUnknownFields = false)
public class ApplicationProperties {
    private int apiTokenValidityInDays;
    private int invitationTokenValidityInDays;
    private int maxInboundMLWorkerMessageMB = 1024;
    private Double borderLineThreshold;
    private Double regressionThreshold;
    private Path home;
    private int externalWorkerHeartbeatIntervalSeconds;
    private String auth;
    private String licensePublicKey;
    private int maxStompMessageSize = 65535;
    private int maxStompReplyMessagePayloadSize = 4096;

    private String mailBaseUrl;
    private String emailFrom;
    private String base64JwtSecretKey;
    private String jwtSecretKey;
    private long tokenValidityInSeconds = 1800; // 30 minutes;
    private long tokenValidityInSecondsForRememberMe = 2592000; // 30 days;
    private CorsConfiguration cors = new CorsConfiguration();

    private String defaultApiKey;
    private String hfDemoSpaceUnlockToken;
    private String mixpanelProjectKey;
}


