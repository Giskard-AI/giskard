package ai.giskard.utils;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collection;

public class YAMLConverter {

    private static ObjectMapper MAPPER = new ObjectMapper(new YAMLFactory());

    private YAMLConverter() {
        throw new IllegalStateException("YAMLConverter is a Utility class. Not meant to be instantiated");
    }

    public static void exportEntityToYAML(Object a, Path p) throws IOException {
        if (!Files.exists(p)) {
            Files.createFile(p);
        }

        MAPPER.writeValue(p.toFile(), a);
    }

    public static void exportEntitiesToYAML(Collection<?> entities, Path p) throws IOException {
        if (!Files.exists(p)) {
            Files.createFile(p);
        }

        MAPPER.writeValue(p.toFile(), entities);
    }

    public static String writeValueAsString(Object data) throws JsonProcessingException {
        return MAPPER.writeValueAsString(data);
    }

}
