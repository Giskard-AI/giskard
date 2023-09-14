package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.service.ee.LicenseService;
import com.mixpanel.mixpanelapi.MessageBuilder;
import com.mixpanel.mixpanelapi.MixpanelAPI;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.NoSuchElementException;

@Service
@RequiredArgsConstructor
public class AnalyticsCollectorService {
    private static final Logger log = LoggerFactory.getLogger(AnalyticsCollectorService.class);

    private static final MixpanelAPI mixpanel = new MixpanelAPI();

    private MessageBuilder messageBuilder;

    private final ApplicationProperties applicationProperties;

    private final GeneralSettingsService settingsService;
    private final LicenseService licenseService;
    @Value("${build.version:-}")
    private String buildVersion;

    private final Runtime.Version javaVersion = Runtime.version();

    @PostConstruct
    public void configure() {
        if (messageBuilder == null) {
            messageBuilder = new MessageBuilder(applicationProperties.getMixpanelProjectKey());
        }
    }

    public void track(String eventName, JSONObject props) {
        if (!settingsService.getSettings().isAnalyticsEnabled()) return;
        doTrack(eventName, props);
    }

    public void track(String eventName, JSONObject props, boolean force) {
        if (force) {
            doTrack(eventName, props);
        } else {
            track(eventName, props);
        }
    }

    public void doTrack(String eventName, JSONObject props) {
        // Refresh user information for MixPanel
        JSONObject serverProps = new JSONObject();
        try {
            serverProps.put("Giskard Instance", settingsService.getSettings().getInstanceId());
            serverProps.put("Giskard Version", buildVersion);
            serverProps.put("Giskard Plan", licenseService.getCurrentLicense().getPlanCode());
            serverProps.put("Giskard LicenseID", licenseService.getCurrentLicense().getId());
            serverProps.put("Is HuggingFace", GeneralSettingsService.isRunningInHFSpaces);
            serverProps.put("HuggingFace Space ID", GeneralSettingsService.hfSpaceId);
            messageBuilder.set(settingsService.getSettings().getInstanceId(), serverProps);
        } catch (NoSuchElementException e) {
            e.printStackTrace();
            return;
        }

        // Start a new thread
        new Thread(() -> {
            // Merge with server info
            props.put("Java version", javaVersion.toString());
            props.put("Giskard version", buildVersion);

            JSONObject message = messageBuilder.event(settingsService.getSettings().getInstanceId(), eventName, props);

            try {
                mixpanel.sendMessage(message);
            } catch (IOException e) {
                log.warn("MixPanel tracking failed {0}", e);
            }
        }).start();
    }

    public static class MLWorkerWebSocketTracking {
        private MLWorkerWebSocketTracking() {}
        public static final String ACTION_TIME_FILED = "action_time";
        public static final String TYPE_FILED = "type";
        public static final String ERROR_FIELD = "error";
        public static final String ERROR_TYPE_FIELD = "error_type";
    }
}
