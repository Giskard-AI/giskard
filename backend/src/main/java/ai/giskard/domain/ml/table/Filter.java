package ai.giskard.domain.ml.table;


import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
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
    private long inspectionId;
    private RowFilterType type;
    @UINullable
    private String[] targetLabel;
    @UINullable
    private String[] predictedLabel;

    @UINullable
    private String thresholdLabel;

    @UINullable
    private Float minThreshold;

    @UINullable
    private Float maxThreshold;

    @UINullable
    private Float minLabelThreshold;

    @UINullable
    private Float maxLabelThreshold;

    @UINullable
    private String regressionUnit;

    @UINullable
    private Float minDiffThreshold;

    @UINullable
    private Float maxDiffThreshold;

}
