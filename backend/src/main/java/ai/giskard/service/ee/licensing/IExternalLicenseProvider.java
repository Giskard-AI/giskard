package ai.giskard.service.ee.licensing;


import ai.giskard.service.ee.FeatureFlagService;

import java.util.HashMap;
import java.util.Map;

public interface IExternalLicenseProvider {
    enum GiskardEdition {
        OPEN_SOURCE,
        STARTUP,
        ENTERPRISE
    }

    class License {
        private final String licenseKey;
        private GiskardEdition edition;
        private final Map<FeatureFlagService.FeatureFlag, Boolean> features;

        public License(String key, GiskardEdition edition) {
            licenseKey = key;
            edition = edition;
            features = new HashMap<>();
        }
    }

    License getLicense();
}
