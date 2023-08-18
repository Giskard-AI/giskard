package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSGeneratedTestSuiteDTO implements MLWorkerWSBaseDTO {
    @JsonProperty("test_uuid")
    private String testUuid;

    private List<MLWorkerWSGeneratedTestInputDTO> inputs;
}
