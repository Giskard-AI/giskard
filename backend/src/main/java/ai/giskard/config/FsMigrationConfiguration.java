package ai.giskard.config;

import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.core.env.Environment;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.Objects;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Consumer;

@Component
@RequiredArgsConstructor
public class FsMigrationConfiguration implements InitializingBean {

    private final Logger log = LoggerFactory.getLogger(FsMigrationConfiguration.class);
    private final Environment env;
    private final ResourceLoader resourceLoader;


    private String getScriptPath(String script) throws IOException {
        Resource resource = Objects.requireNonNull(resourceLoader.getResource("classpath:./config/fs/" + script),
            "Script not found");
        return resource.getFile().getPath();
    }


    @Override
    public void afterPropertiesSet() throws Exception {
        boolean isWindows = System.getProperty("os.name").toLowerCase().startsWith("windows");

        if (isWindows) {
            // It's not an issue since it should be run on docker for production environment
            log.info("Skipping file system migrations on windows");
            return;
        }

        log.info("Executing file system migrations");

        ExecutorService executorService = Executors.newSingleThreadExecutor();

        Process process = new ProcessBuilder("/bin/sh", "-c", getScriptPath("flatten-artifacts.sh"), "-h", env.getProperty("giskard.home"))
            .start();

        StreamGobbler streamGobbler = new StreamGobbler(process.getInputStream(), value -> {
        });

        executorService.submit(streamGobbler);

        int exitCode = process.waitFor();
        if (exitCode != 0) {
            throw new RuntimeException("Unable to execute script: flatten-artifacts.sh");
        }
    }

    private record StreamGobbler(InputStream inputStream, Consumer<String> consumer) implements Runnable {
        @Override
        public void run() {
            new BufferedReader(new InputStreamReader(inputStream))
                .lines()
                .forEach(consumer);
        }
    }


}

