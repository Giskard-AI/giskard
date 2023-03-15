package ai.giskard.web.rest.controllers.ee;

import ai.giskard.service.ee.LicenseService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/ee")
public class LicenseController {

    private final LicenseService licenseService;

    @PostMapping("/license")
    public void uploadLicense(@RequestPart MultipartFile file) throws IOException {
        String fileString = new String(file.getBytes());
        licenseService.uploadLicense(fileString);
    }
}
