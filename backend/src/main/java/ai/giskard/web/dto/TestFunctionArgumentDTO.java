package ai.giskard.web.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class TestFunctionArgumentDTO {
    String name;
    String type;
    boolean optional;
    @JsonAlias("default")
    String defaultValue;
    int argOrder;


}
