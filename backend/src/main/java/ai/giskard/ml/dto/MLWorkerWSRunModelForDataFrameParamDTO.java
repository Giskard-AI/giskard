package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.Map;

@Getter
@Setter
@Builder
public class MLWorkerWSRunModelForDataFrameParamDTO implements MLWorkerWSBaseDTO {
    private MLWorkerWSArtifactRefDTO model;

    private MLWorkerWSDataFrameDTO dataframe;

    private String target;

    @JsonProperty("column_types")
    private Map<String, String> columnTypes;

    @JsonProperty("column_dtypes")
    private Map<String, String> columnDtypes;
}
