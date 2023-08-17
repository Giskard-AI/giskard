package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Builder
public class MLWorkerWSGenerateTestSuiteParamDTO implements MLWorkerWSBaseDTO {
    @JsonProperty("project_key")
    private String projectKey;

    private List<MLWorkerWSSuiteInputDTO> inputs;
}
