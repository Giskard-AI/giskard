package ai.giskard.web.rest.controllers;

import ai.giskard.web.dto.ApplicationConfigDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.info.BuildProperties;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/config")
public class ConfigurationController {
    private final BuildProperties buildProperties;

    @GetMapping("")
    public ApplicationConfigDTO getConfig() {
        return ApplicationConfigDTO.builder()
            .giskardVersion(buildProperties.getVersion())
            .build();
    }

}
