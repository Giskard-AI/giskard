package ai.giskard.web.dto;

import ai.giskard.domain.ColumnType;
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
    private Map<String, ColumnType> columnTypes;
    private Map<String, String> columnDtypes;
    private String target;
}
