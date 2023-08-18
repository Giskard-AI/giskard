package ai.giskard.ml.dto;

import ai.giskard.service.GiskardRuntimeException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

public class MLWorkerWSUtils {
    public static <T> T convertMLWorkerWSObject(MLWorkerWSBaseDTO object, Class<T> clazz) {
        try {
            return new ObjectMapper().readValue(new ObjectMapper().writeValueAsString(object), clazz);
        } catch (JsonProcessingException e) {
            throw new GiskardRuntimeException("Failed to convert MLWorker WebSocket object", e);
        }
    }

    private MLWorkerWSUtils() {}
}
