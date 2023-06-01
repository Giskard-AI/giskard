package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Data;

import java.util.List;

@Data
@UIModel
public class DatasetProcessingResultDTO {
    private String datasetId;
    private int totalRows;
    private List<Integer> filteredRows;
    private List<TransformationResultMessageDTO> modifications;
}
