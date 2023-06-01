package ai.giskard.service.ee;

import ai.giskard.config.ApplicationProperties;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.EnumMap;
import java.util.Map;

import static ai.giskard.service.ee.FeatureFlagService.FeatureFlag.AUTH;

@Service
@RequiredArgsConstructor
public class FeatureFlagService {
    private final ApplicationProperties applicationProperties;

    public enum FeatureFlag {
        AUTH
    }

    /**
     * This method is a stub and currently returns default values. It needs to be implemented properly, by checking
     * license and other things.
     *
     * @return a map of featureflag => boolean
     */
    public Map<FeatureFlag, Boolean> getAllFeatures() {
        Map<FeatureFlag, Boolean> features = new EnumMap<>(FeatureFlag.class);
        String giskardAuth;
        giskardAuth = applicationProperties.getAuth();
        if (giskardAuth == null) {
            giskardAuth = System.getenv("GISKARD_AUTH");
        }
        features.put(AUTH, giskardAuth != null && giskardAuth.equals("true"));
        return features;
    }

    public boolean hasFlag(FeatureFlag flag) {
        return getAllFeatures().get(flag);
    }
}
