package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSGenerateTestSuiteDTO implements MLWorkerWSBaseDTO {
    private List<MLWorkerWSGeneratedTestSuiteDTO> tests;
}
