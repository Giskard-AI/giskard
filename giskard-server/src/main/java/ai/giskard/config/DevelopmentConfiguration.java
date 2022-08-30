package ai.giskard.config;

import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.info.BuildProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Properties;

@Configuration
public class DevelopmentConfiguration {
    // This is a hacky way to overcome an Intellij issue described here
    // https://stackoverflow.com/questions/56634081/failed-autowired-of-buildproperties-spring-boot-2-1-5-eclipse
    // Without switching to "Build and run using: Gradle" in the Intellij settings that makes project startup longer
    @Bean
    @ConditionalOnMissingBean(BuildProperties.class)
    BuildProperties buildProperties() {
        return new BuildProperties(new Properties());
    }
}
