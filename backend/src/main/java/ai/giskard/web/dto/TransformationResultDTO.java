package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Data;

import java.util.List;

@Data
@UIModel
public class TransformationResultDTO {

    private int totalRow;
    private int modifiedRow;
    private List<DatasetDescribeColumnDTO> describeColumns;
}
