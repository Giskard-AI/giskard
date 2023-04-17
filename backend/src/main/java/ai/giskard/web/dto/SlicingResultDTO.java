package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Data;

import java.util.List;

@Data
@UIModel
public class SlicingResultDTO {

    private int totalRow;
    private int filteredRow;
    private List<DatasetDescribeColumnDTO> describeColumns;
}
