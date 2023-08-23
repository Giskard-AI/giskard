package ai.giskard;

import org.springframework.boot.SpringApplication;

public class GiskardTestApp {
    public static void main(String[] args) {
        SpringApplication.from(GiskardApp::main)
            .with(RunContainersConfiguration.class)
            .run(args);
    }
}
