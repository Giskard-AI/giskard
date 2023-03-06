package ai.giskard.web.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import javax.validation.constraints.NotBlank;

@Data
public class TestInputDTO {

    @NotBlank
    private String name;
    private String value;
    @JsonAlias("is_alias")
    @JsonProperty("isAlias")
    private boolean isAlias;
}
