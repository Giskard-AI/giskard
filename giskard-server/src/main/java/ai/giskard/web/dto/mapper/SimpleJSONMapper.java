package ai.giskard.web.dto.mapper;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.mapstruct.Named;

import java.util.List;
import java.util.Map;

@Named("SimpleJSON")
public class SimpleJSONMapper {
    public static List<String> toListOfStrings(String str) throws JsonProcessingException {
        return new ObjectMapper().readValue(str, new TypeReference<>() {
        });
    }

    public static Map<String, String> toMapStringString(String str) throws JsonProcessingException {
        return new ObjectMapper().readValue(str, new TypeReference<>() {
        });
    }

}
