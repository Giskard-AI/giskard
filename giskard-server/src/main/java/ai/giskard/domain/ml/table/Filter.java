package ai.giskard.domain.ml.table;


import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * TODO Inheritance for classif regression..
 */
@UIModel
@Getter
@Setter
@NoArgsConstructor
public class Filter {

    private RowFilterType rowFilter;

    private String[] targetLabel;

    private String[] predictedLabel;

    private String thresholdLabel;

    private Float minThreshold;

    private Float maxThreshold;

    private Float minLabelThreshold;

    private Float maxLabelThreshold;

    private String regressionUnit;

    private Float minDiffThreshold;

    private Float maxDiffThreshold;
}
