package ai.giskard.utils;

import ai.giskard.service.GiskardRuntimeException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.NoArgsConstructor;
import org.mapstruct.Named;

@NoArgsConstructor
@Named("json")
public class JSON {

    public static String toJSON(Object o) {
        try {
            return new ObjectMapper().writeValueAsString(o);
        } catch (JsonProcessingException e) {
            throw new GiskardRuntimeException("Failed to serialize JSON", e);
        }
    }

    public static <T> T fromJSON(String jsonString, TypeReference<T> valueTypeRef) {
        if (jsonString == null) {
            return null;
        }
        try {
            return new ObjectMapper().readValue(jsonString, valueTypeRef);
        } catch (JsonProcessingException e) {
            throw new GiskardRuntimeException("Failed to deserialize JSON", e);
        }
    }
}
