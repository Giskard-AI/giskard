package ai.giskard;

import ai.giskard.config.ApplicationProperties;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.liquibase.LiquibaseProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

@SpringBootApplication
@EnableConfigurationProperties({LiquibaseProperties.class, ApplicationProperties.class})
@EnableJpaAuditing
@RequiredArgsConstructor
public class GiskardTestApp {
    public static void main(String[] args) {
        SpringApplication.from(GiskardApp::main)
            .with(RunContainersConfiguration.class)
            .run(args);
    }
}
