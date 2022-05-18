package ai.giskard.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;

import java.nio.file.Path;

/**
 * Properties specific to Giskard.
 * <p>
 * Properties are configured in the {@code application.yml} file.
 * See {@link tech.jhipster.config.JHipsterProperties} for a good example.
 */
@Setter
@Getter
@ConfigurationProperties(prefix = "application", ignoreUnknownFields = false)
public class ApplicationProperties {
    private String mlWorkerHost;
    private int mlWorkerPort;
    private int apiTokenValidityInDays;
    private int invitationTokenValidityInDays;
    private String bucketPath;
    private Double borderLineThreshold;
    private Double regressionThreshold;

    private Path giskardHome;
}
