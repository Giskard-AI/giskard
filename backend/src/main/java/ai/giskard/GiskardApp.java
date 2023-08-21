package ai.giskard;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.config.GiskardConstants;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.liquibase.LiquibaseProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.core.env.Environment;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

import javax.annotation.PostConstruct;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.Arrays;
import java.util.Collection;
import java.util.Map;
import java.util.Optional;

@SpringBootApplication
@EnableConfigurationProperties({LiquibaseProperties.class, ApplicationProperties.class})
@EnableJpaAuditing
public class GiskardApp {

    private static final Logger log = LoggerFactory.getLogger(GiskardApp.class);

    private final Environment env;

    public GiskardApp(Environment env) {
        this.env = env;
    }

    /**
     * Initializes giskard.
     * <p>
     * Spring profiles can be configured with a program argument --spring.profiles.active=your-active-profile
     * <p>
     */
    @PostConstruct
    public void initApplication() {
        Collection<String> activeProfiles = Arrays.asList(env.getActiveProfiles());
        if (
            activeProfiles.contains(GiskardConstants.SPRING_PROFILE_DEVELOPMENT) &&
                activeProfiles.contains(GiskardConstants.SPRING_PROFILE_PRODUCTION)
        ) {
            log.error(
                "You have misconfigured your application! It should not run " + "with both the 'dev' and 'prod' profiles at the same time."
            );
        }
        if (
            activeProfiles.contains(GiskardConstants.SPRING_PROFILE_DEVELOPMENT) &&
                activeProfiles.contains(GiskardConstants.SPRING_PROFILE_CLOUD)
        ) {
            log.error(
                "You have misconfigured your application! It should not " + "run with both the 'dev' and 'cloud' profiles at the same time."
            );
        }
    }

    /**
     * Main method, used to run the application.
     *
     * @param args the command line arguments.
     */
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(GiskardApp.class);
        app.setDefaultProperties(Map.of("spring.profiles.default", GiskardConstants.SPRING_PROFILE_DEVELOPMENT));

        ConfigurableApplicationContext ctx = app.run(args);
        logApplicationStartup(ctx.getEnvironment());
    }

    private static void logApplicationStartup(Environment env) {
        String protocol = Optional.ofNullable(env.getProperty("server.ssl.key-store")).map(key -> "https").orElse("http");
        String serverPort = env.getProperty("server.port");
        String contextPath = Optional
            .ofNullable(env.getProperty("server.servlet.context-path"))
            .filter(StringUtils::isNotBlank)
            .orElse("/");
        String hostAddress = "localhost";
        try {
            hostAddress = InetAddress.getLocalHost().getHostAddress();
        } catch (UnknownHostException e) {
            log.warn("The host name could not be determined, using `localhost` as fallback");
        }
        String[] profiles = env.getActiveProfiles().length == 0 ? env.getDefaultProfiles() : env.getActiveProfiles();
        boolean hasApiDocsProfile = Arrays.asList(profiles).contains("api-docs");
        String giskardHome = env.getProperty("giskard.home");
        double totalMemory = bytesToMB(Runtime.getRuntime().totalMemory());
        double maxMemory = bytesToMB(Runtime.getRuntime().maxMemory());
        double freeMemory = bytesToMB(Runtime.getRuntime().freeMemory());
        String memoryStatusLine = String.format("""
            Memory status:
            \tTotal: %s MB
            \tMax: %s MB
            \tFree: %s MB""", totalMemory, maxMemory, freeMemory);
        String swaggerURL = hasApiDocsProfile ? String.format("Swagger UI: %s://localhost:%s%sswagger-ui/index.html\t%n\t", protocol, serverPort, contextPath) : "";
        log.info(
            "\n----------------------------------------------------------\n\t" +
                memoryStatusLine +
                "\n----------------------------------------------------------\n\t" +
                "Application '{}' is running! Access URLs:\n\t" +
                "Local: \t\t{}://localhost:{}{}\n\t" +
                "External: \t{}://{}:{}{}\n\t" +
                swaggerURL +
                "Giskard Home: " + giskardHome + "\n\t" +
                "Profile(s): \t{}\n----------------------------------------------------------",
            env.getProperty("spring.application.name"),
            protocol,
            serverPort,
            contextPath,
            protocol,
            hostAddress,
            serverPort,
            contextPath,
            profiles
        );
    }

    private static long bytesToMB(long totalMemory) {
        return totalMemory / 1024 / 1024;
    }
}
