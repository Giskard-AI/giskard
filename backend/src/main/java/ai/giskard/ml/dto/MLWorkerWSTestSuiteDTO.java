package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSTestSuiteDTO implements MLWorkerWSBaseDTO {
    @JsonProperty("is_error")
    private Boolean isError;

    @JsonProperty("is_pass")
    private Boolean isPass;

    private List<MLWorkerWSIdentifierSingleTestResultDTO> results;

    private String logs;
}
