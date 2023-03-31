package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import javax.validation.constraints.NotBlank;

@Data
public class TestInputDTO {

    @NotBlank
    private String name;
    @UINullable
    private String value;
    private String type;
    @JsonAlias("is_alias")
    @JsonProperty("isAlias")
    private boolean isAlias;
}
