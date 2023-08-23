package ai.giskard;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.devtools.restart.RestartScope;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.context.annotation.Bean;
import org.testcontainers.containers.BindMode;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.containers.wait.strategy.LogMessageWaitStrategy;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

@TestConfiguration(proxyBeanMethods = false)
public class RunContainersConfiguration {
    @Value("${spring.datasource.username:giskard}")
    private String pgUsername;
    @Value("${spring.datasource.password:giskard}")
    private String pgPassowrd;


    @Bean
    @ServiceConnection
    @RestartScope
    PostgreSQLContainer<?> postgreSQLContainer() {


        List<String> portBindings = new ArrayList<>();
        portBindings.add("15432:5432"); // hostPort:containerPort

        PostgreSQLContainer<?> pgContainer = new PostgreSQLContainer<>("postgres:13")
            .withReuse(true)
            .withUsername(pgUsername)
            .withPassword(pgPassowrd)
            .withDatabaseName("giskard")
            .withStartupTimeout(java.time.Duration.ofSeconds(60))
            .withFileSystemBind(resolveFromHome(Paths.get("giskard-home", "database")), "/var/lib/postgresql/data", BindMode.READ_WRITE);

        pgContainer.setPortBindings(portBindings);
        pgContainer.setWaitStrategy(new LogMessageWaitStrategy().withRegEx(".*database system is ready to accept connections.*"));

        return pgContainer;
    }

    private String resolveFromHome(Path path) {
        return Paths.get(System.getProperty("user.home")).resolve(path).toString();
    }

}
