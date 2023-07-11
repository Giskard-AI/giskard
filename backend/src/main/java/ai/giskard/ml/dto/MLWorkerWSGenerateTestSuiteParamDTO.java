package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class MLWorkerWSGenerateTestSuiteParamDTO implements MLWorkerWSBaseDTO {
    @JsonProperty("project_key")
    String projectKey;

    List<MLWorkerWSSuiteInputDTO> inputs;
}
