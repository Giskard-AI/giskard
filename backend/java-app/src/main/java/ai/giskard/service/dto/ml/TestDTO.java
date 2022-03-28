package ai.giskard.service.dto.ml;

import ai.giskard.domain.ml.CodeLanguage;
import ai.giskard.domain.ml.TestType;
import ai.giskard.domain.ml.testing.Test;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;

@Setter
@Getter
@NoArgsConstructor
public class TestDTO {
    private Long id;

    @NotNull
    private String name;

    private String code;

    private CodeLanguage language;

    private Long testSuiteId;

    private TestType type;

    public TestDTO(Test test) {
        id = test.getId();
        name = test.getName();
        code = test.getCode();
        language = test.getLanguage();
        testSuiteId = test.getTestSuite().getId();
        type = test.getType();
    }
}
