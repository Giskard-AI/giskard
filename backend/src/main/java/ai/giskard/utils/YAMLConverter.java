package ai.giskard.utils;

import ai.giskard.domain.BaseEntity;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;

public class YAMLConverter {
    public static void exportEntityToYAML(BaseEntity a, Path p) throws IOException{
        if (!Files.exists(p)){
            Files.createFile(p);
        }
        ObjectMapper mapper = new ObjectMapper(new YAMLFactory());
        mapper.writeValue(p.toFile(), a);
    }

    public static void exportEntitiesToYAML(Set<? extends BaseEntity> entities, Path p) throws IOException{
        if (!Files.exists(p)){
            Files.createFile(p);
        }
        ObjectMapper mapper = new ObjectMapper(new YAMLFactory());
        mapper.writeValue(p.toFile(), entities);
    }
}
