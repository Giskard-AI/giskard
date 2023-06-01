package ai.giskard.web.dto.ml;

import ai.giskard.domain.ColumnType;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class DatasetDTO {
    @UINullable
    private String target;
    @JsonAlias("column_types")
    private Map<String, ColumnType> columnTypes;
    @JsonIgnore
    private ProjectDTO project;
    @JsonProperty("id")
    @NotNull
    private UUID id;
    private String name;
    @JsonAlias("column_dtypes")
    private Map<String, String> columnDtypes;
    @JsonAlias("original_size_bytes")
    private int originalSizeBytes;
    @JsonAlias("compressed_size_bytes")
    private int compressedSizeBytes;

    @JsonAlias("created_date")
    private Instant createdDate;
}
