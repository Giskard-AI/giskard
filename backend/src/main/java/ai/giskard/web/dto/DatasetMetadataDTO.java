package ai.giskard.web.dto;

import ai.giskard.domain.ColumnType;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
@UIModel
@AllArgsConstructor
public class DatasetMetadataDTO {
    private String name;
    private UUID id;
    @UINullable
    private String target;
    @JsonAlias("column_types")
    private Map<String, ColumnType> columnTypes;
    @UINullable
    @JsonAlias("column_dtypes")
    private Map<String, String> columnDtypes;
    private long numberOfRows;
    private Map<String, List<String>> categoryFeatures;
}
