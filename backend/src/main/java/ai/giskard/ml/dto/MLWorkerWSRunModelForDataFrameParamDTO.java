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
    MLWorkerWSArtifactRefDTO model;

    MLWorkerWSDataFrameDTO dataframe;

    String target;

    @JsonProperty("column_types")
    Map<String, String> columnTypes;

    @JsonProperty("column_dtypes")
    Map<String, String> columnDtypes;
}
