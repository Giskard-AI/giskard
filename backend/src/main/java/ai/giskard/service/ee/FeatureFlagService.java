package ai.giskard.service.ee;

import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

import static ai.giskard.service.ee.FeatureFlagService.FeatureFlag.Auth;

// TODO: see how to handle that with API


@Service
public class FeatureFlagService {

    public enum FeatureFlag {
        Auth
    }

    /**
     * This method is a stub and currently returns default values. It needs to be implemented properly, by checking
     * license and other things.
     *
     * @return
     */
    public Map<FeatureFlag, Boolean> getAllFeatures() {
        Map<FeatureFlag, Boolean> features = new HashMap<>();
        features.put(Auth, false);
        return features;
    }

    public boolean hasFlag(FeatureFlag flag) {
        return getAllFeatures().get(flag);
    }
}
