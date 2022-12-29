package ai.giskard.service.ee;

import org.springframework.stereotype.Service;

// TODO: see how to handle that with API


@Service
public class FeatureFlagService {

    public enum FeatureFlag {
        AUTH
    }

    /**
     *  THIS METHOD IS CURRENTLY A STUB AND DOES NOT FUNCTION FOR REAL
     * @param flag
     * @return
     */
    public boolean hasFeature(FeatureFlag flag) {
        // TODO: External API call to 3rd party?
        if (flag == FeatureFlag.AUTH) {
            return false;
        }

        return true;
    }
}
