package ai.giskard.web.rest;

import ai.giskard.service.UserService;
import ai.giskard.service.dto.AdminUserDTO;
import ai.giskard.service.dto.UserDTO;
import ai.giskard.service.dto.config.AppConfigDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
public class AppConfigController {
    private final Logger log = LoggerFactory.getLogger(AppConfigController.class);
    private UserService userService;

    public AppConfigController(UserService userService) {
        this.userService = userService;
    }

    // TODO andreyavtomonov (12/03/2022): change url to more explainable
    @GetMapping("/users/me")
    public AppConfigDTO getApplicationSettings() {
        log.debug("REST request to get all public User names");
        AdminUserDTO userDTO = userService
            .getUserWithAuthorities()
            .map(AdminUserDTO::new)
            .orElseThrow(() -> new RuntimeException("User could not be found"));
        return new AppConfigDTO(
            new AppConfigDTO.AppInfoDTO("basic", "Basic", 1),
            userDTO);
    }

}
