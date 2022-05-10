package ai.giskard.domain.ml.table;


import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@UIModel
@Getter
@Setter
@NoArgsConstructor
public class Filter {

    private RowFilterType rowFilter;

    private String target;

    private String predicted;

    private Float minThreshold;

    private Float maxThreshold;
}
