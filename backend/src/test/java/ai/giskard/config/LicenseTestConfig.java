package ai.giskard.config;

import ai.giskard.service.ee.FeatureFlag;
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
        mockLicense.setActive(true);

        LicenseService mock = Mockito.mock(LicenseService.class);
        Mockito.when(mock.getCurrentLicense()).thenReturn(mockLicense);
        Mockito.when(mock.hasFeature(Mockito.any(FeatureFlag.class)))
            .thenAnswer(invocation -> {
                FeatureFlag flag = invocation.getArgument(0);
                return mockLicense.hasFeature(flag);
            });
        return mock;
    }

}
