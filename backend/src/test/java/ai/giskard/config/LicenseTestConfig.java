package ai.giskard.config;

import ai.giskard.service.ee.License;
import ai.giskard.service.ee.LicenseService;
import org.mockito.Mockito;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

import java.util.Collections;

@Configuration
public class LicenseTestConfig {

    @Bean
    @Primary
    public LicenseService licenseService() {
        License mockLicense = new License();
        mockLicense.setFeatures(Collections.singletonList("AUTH"));

        LicenseService mock = Mockito.mock(LicenseService.class);
        Mockito.when(mock.getCurrentLicense()).thenReturn(mockLicense);
        return mock;
    }

}
