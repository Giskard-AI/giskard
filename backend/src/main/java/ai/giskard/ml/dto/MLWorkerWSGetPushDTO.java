package ai.giskard.ml.dto;

import ai.giskard.domain.ml.CallToActionKind;
import ai.giskard.domain.ml.PushKind;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import javax.annotation.Nullable;
import java.util.Map;

@Getter
@Setter
@Builder
public class MLWorkerWSGetPushDTO implements MLWorkerWSBaseDTO {
    private MLWorkerWSArtifactRefDTO dataset;
    private MLWorkerWSArtifactRefDTO model;
    private int rowIdx;
    private MLWorkerWSDataFrameDTO dataframe;

    private String target;

    @JsonProperty("column_types")
    private Map<String, String> columnTypes;

    @JsonProperty("column_dtypes")
    private Map<String, String> columnDtypes;
    @Nullable
    @JsonProperty("push_kind")
    private PushKind pushKind;
    @Nullable
    @JsonProperty("cta_kind")
    private CallToActionKind ctaKind;
}
