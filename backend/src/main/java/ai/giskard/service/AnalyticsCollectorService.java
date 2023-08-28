package ai.giskard.service;

import ai.giskard.config.GiskardConstants;
import ai.giskard.service.ee.LicenseService;
import com.mixpanel.mixpanelapi.MessageBuilder;
import com.mixpanel.mixpanelapi.MixpanelAPI;
import lombok.RequiredArgsConstructor;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Service;

import java.util.Arrays;
import java.util.Collection;

@Service
@RequiredArgsConstructor
public class AnalyticsCollectorService {
    private static final Logger log = LoggerFactory.getLogger(AnalyticsCollectorService.class);

    private static final String DEV_MP_PROJECT_KEY = "4cca5fabca54f6df41ea500e33076c99";
    private static final String PROD_MP_PROJECT_KEY = "2c3efacc6c26ffb991a782b476b8c620";

    private static final MixpanelAPI mixpanel = new MixpanelAPI();

    private final MessageBuilder messageBuilderDev = new MessageBuilder(DEV_MP_PROJECT_KEY);
    private final MessageBuilder messageBuilder = new MessageBuilder(PROD_MP_PROJECT_KEY);

    private String activeProfile = GiskardConstants.SPRING_PROFILE_DEVELOPMENT;

    private final GeneralSettingsService settingsService;
    private final LicenseService licenseService;
    @Value("${build.version:-}")
    private String buildVersion;

    public void configure(Environment env) {
        Collection<String> activeProfiles = Arrays.asList(env.getActiveProfiles());

        // Prepare user information for MixPanel
        JSONObject serverProps = new JSONObject();
        serverProps.put("Giskard Instance", settingsService.getSettings().getInstanceId());
        serverProps.put("Giskard Version", buildVersion);
        serverProps.put("Giskard Plan", licenseService.getCurrentLicense().getPlanCode());
        serverProps.put("Giskard LicenseID", licenseService.getCurrentLicense().getId());
        serverProps.put("Is HuggingFace", GeneralSettingsService.isRunningInHFSpaces);
        serverProps.put("HuggingFace Space ID", GeneralSettingsService.hfSpaceId);

        if (activeProfiles.contains(GiskardConstants.SPRING_PROFILE_DEVELOPMENT)) {
            this.activeProfile = GiskardConstants.SPRING_PROFILE_DEVELOPMENT;
            messageBuilderDev.set(settingsService.getSettings().getInstanceId(), serverProps);
        } else {
            this.activeProfile = GiskardConstants.SPRING_PROFILE_PRODUCTION;
            messageBuilder.set(settingsService.getSettings().getInstanceId(), serverProps);
        }
    }
}
