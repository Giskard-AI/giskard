package ai.giskard.web.dto;

import ai.giskard.domain.ColumnType;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.Data;

@Data
@UIModel
public class ColumnFilterDTO {

    private String column;
    private ColumnType columnType;
    private NoCodeSlicingType slicingType;
    @UINullable
    private String value;

}
