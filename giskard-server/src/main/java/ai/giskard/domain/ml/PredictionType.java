package ai.giskard.domain.ml;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;

@UIModel
@AllArgsConstructor
public enum PredictionType {
    REGRESSION("regression"),
    CLASSIFICATION("classification");
    @Getter
    private final String name;
}
