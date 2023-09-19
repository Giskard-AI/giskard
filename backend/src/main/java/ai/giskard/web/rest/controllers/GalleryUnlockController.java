package ai.giskard.web.rest.controllers;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.service.InitService;
import ai.giskard.web.dto.GalleryUnlockDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.Objects;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/hfs/unlock")
public class GalleryUnlockController {
    private final ApplicationProperties applicationProperties;

    @GetMapping("")
    public GalleryUnlockDTO getUnlockStatus() {
        GalleryUnlockDTO unlockDTO = new GalleryUnlockDTO();
        unlockDTO.setUnlocked(InitService.isUnlocked());
        unlockDTO.setToken(null);
        return unlockDTO;
    }

    @PostMapping("")
    public GalleryUnlockDTO setUnlockStatus(@RequestBody GalleryUnlockDTO unlockDTO) {
        if (StringUtils.hasText(unlockDTO.getToken()) &&
            Objects.equals(unlockDTO.getToken(), applicationProperties.getHfDemoSpaceUnlockToken())) {
            InitService.setUnlocked(unlockDTO.isUnlocked());
            unlockDTO.setUnlocked(InitService.isUnlocked());
            unlockDTO.setToken(null);
            return unlockDTO;
        }
        throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Invalid unlock token");
    }
}
