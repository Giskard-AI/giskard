package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.CodeLanguage;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.Setter;

import jakarta.validation.constraints.NotNull;

@UIModel
public class CodeBasedTestPresetDTO {
    @lombok.Setter
    @lombok.Getter
    private Long id;

    @Getter
    @Setter
    @NotNull
    private String name;

    @Getter
    @Setter
    private String code;

    @Getter
    @Setter
    private CodeLanguage language;
}
