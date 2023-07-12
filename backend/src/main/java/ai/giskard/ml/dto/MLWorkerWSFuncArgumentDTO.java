package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Builder
public class MLWorkerWSFuncArgumentDTO implements MLWorkerWSBaseDTO {
    private String name;

    @JsonInclude(JsonInclude.Include.NON_NULL)
    private MLWorkerWSArtifactRefDTO model;

    @JsonInclude(JsonInclude.Include.NON_NULL)
    private MLWorkerWSArtifactRefDTO dataset;

    @JsonProperty("float")
    @JsonInclude(JsonInclude.Include.NON_NULL)
    private Float floatValue;

    @JsonProperty("int")
    @JsonInclude(JsonInclude.Include.NON_NULL)
    private Integer intValue;

    @JsonProperty("str")
    @JsonInclude(JsonInclude.Include.NON_NULL)
    private String strValue;

    @JsonProperty("bool")
    @JsonInclude(JsonInclude.Include.NON_NULL)
    private Boolean boolValue;

    @JsonInclude(JsonInclude.Include.NON_NULL)
    private MLWorkerWSArtifactRefDTO slicingFunction;

    @JsonInclude(JsonInclude.Include.NON_NULL)
    private MLWorkerWSArtifactRefDTO transformationFunction;

    @JsonInclude(JsonInclude.Include.NON_NULL)
    private String kwargs;

    private List<MLWorkerWSFuncArgumentDTO> args;
    private Boolean none;
}
