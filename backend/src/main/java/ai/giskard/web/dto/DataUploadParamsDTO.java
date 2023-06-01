package ai.giskard.web.dto;

import ai.giskard.domain.ColumnMeaning;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.*;

import java.util.Map;

@UIModel
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DataUploadParamsDTO {
    private String name;
    private String projectKey;
    private Map<String, ColumnMeaning> columnMeanings;
    private Map<String, String> columnTypes;
    private String target;
}
