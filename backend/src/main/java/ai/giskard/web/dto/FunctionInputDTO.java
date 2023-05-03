package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import java.util.List;

@Data
public class FunctionInputDTO {

    @NotBlank
    private String name;
    @UINullable
    private String value;
    private String type;
    @JsonAlias("is_alias")
    @JsonProperty("isAlias")
    private boolean isAlias;
    private List<FunctionInputDTO> params;
}
