package ai.giskard.service;

import ai.giskard.domain.GeneralSettings;
import ai.giskard.domain.SerializedGiskardGeneralSettings;
import ai.giskard.repository.GeneralSettingsRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.Optional;
import java.util.stream.Stream;

@Service
@RequiredArgsConstructor
public class GeneralSettingsService {
    private final Logger log = LoggerFactory.getLogger(GeneralSettingsService.class);

    private final GeneralSettingsRepository settingsRepository;

    public static final boolean isRunningInHFSpaces = Stream.of("SPACE_REPO_NAME", "SPACE_ID", "SPACE_HOST").allMatch(System.getenv()::containsKey);

    public static final String hfSpaceId = System.getenv().get("SPACE_ID");

    public GeneralSettings getSettings() {
        return deserializeSettings(settingsRepository.getMandatoryById(SerializedGiskardGeneralSettings.SINGLE_ID).getSettings());
    }

    public GeneralSettings save(GeneralSettings settings) {
        SerializedGiskardGeneralSettings entity = new SerializedGiskardGeneralSettings(serializeSettings(settings));
        return deserializeSettings(settingsRepository.save(entity).getSettings());
    }

    public void saveIfNotExists(GeneralSettings settings) {
        Optional<SerializedGiskardGeneralSettings> result = settingsRepository.findById(SerializedGiskardGeneralSettings.SINGLE_ID);
        if (result.isEmpty()) {
            save(settings);
            log.info("Saved general settings: {}", settings);
        } else {
            String savedSettings = result.get().getSettings();
            GeneralSettings generalSettings = deserializeSettings(savedSettings);
            String newSettings = serializeSettings(generalSettings);
            if (!savedSettings.equals(newSettings)) {
                log.info("Missing some default settings, updating it. Current version: {}, new version: {}", savedSettings, newSettings);
                save(generalSettings);
            }
        }
    }

    private GeneralSettings deserializeSettings(String serializedSettings) {
        try {
            return new ObjectMapper().readValue(serializedSettings, GeneralSettings.class);
        } catch (JsonProcessingException e) {
            throw new GiskardRuntimeException("Failed to deserialize general settings", e);
        }
    }

    private String serializeSettings(GeneralSettings settings) {
        String serializedSettings;
        try {
            ObjectMapper mapper = new ObjectMapper();
            mapper.configure(SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS, true);
            serializedSettings = mapper.writeValueAsString(settings);
        } catch (JsonProcessingException e) {
            throw new GiskardRuntimeException("Failed to serialize general settings", e);
        }
        return serializedSettings;
    }
}
