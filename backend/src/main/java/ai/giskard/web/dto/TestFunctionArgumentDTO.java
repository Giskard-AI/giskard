package ai.giskard.web.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

@Data
public class TestFunctionArgumentDTO {
    String name;
    String type;
    boolean optional;

    @JsonAlias("default")
    String defaultValue;

}
