package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@UIModel
@AllArgsConstructor
public class DatasetPageDTO {

    private int totalItems;
    private List<Map<String, Object>> content;

}
