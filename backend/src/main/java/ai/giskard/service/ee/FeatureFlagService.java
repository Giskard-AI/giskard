package ai.giskard.service.ee;

import org.springframework.stereotype.Service;

import java.util.EnumMap;
import java.util.Map;

import static ai.giskard.service.ee.FeatureFlagService.FeatureFlag.Auth;

@Service
public class FeatureFlagService {

    public enum FeatureFlag {
        Auth
    }

    /**
     * This method is a stub and currently returns default values. It needs to be implemented properly, by checking
     * license and other things.
     *
     * @return a map of featureflag => boolean
     */
    public Map<FeatureFlag, Boolean> getAllFeatures() {
        Map<FeatureFlag, Boolean> features = new EnumMap<>(FeatureFlag.class);
        String giskardAuth = System.getenv("GISKARD_AUTH");
        features.put(Auth, giskardAuth != null && giskardAuth.equals("true"));
        return features;
    }

    public boolean hasFlag(FeatureFlag flag) {
        return getAllFeatures().get(flag);
    }
}
