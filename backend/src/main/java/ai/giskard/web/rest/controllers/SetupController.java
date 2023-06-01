package ai.giskard.web.rest.controllers;

import ai.giskard.domain.GeneralSettings;
import ai.giskard.service.GeneralSettingsService;
import ai.giskard.service.ee.LicenseService;
import ai.giskard.web.dto.SetupDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/setup")
public class SetupController {
    private final GeneralSettingsService settingsService;
    private final LicenseService licenseService;

    @PostMapping("")
    public void finalizeSetup(@RequestBody SetupDTO body) throws IOException {
        // THIS ENDPOINT DOES NOTHING ONCE WE ARE SETUP!
        if (licenseService.getCurrentLicense().isActive()) {
            return;
        }

        GeneralSettings settings = settingsService.getSettings();
        settings.setAnalyticsEnabled(body.isAllowAnalytics());
        settingsService.save(settings);
        licenseService.uploadLicense(body.getLicense());
    }
}
