package ai.giskard.domain.ml.table;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;

@UIModel
@AllArgsConstructor
public enum RegressionUnit {
    ABSDIFF("absDiff"),
    ABSDIFFPERCENT("absDiffPercent");
    @Getter
    private final String name;
}
