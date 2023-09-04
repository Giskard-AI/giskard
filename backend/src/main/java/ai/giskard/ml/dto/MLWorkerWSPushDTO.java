package ai.giskard.ml.dto;

import ai.giskard.domain.ml.PushKind;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;

import javax.annotation.Nullable;
import java.util.List;

@Getter
@Setter
public class MLWorkerWSPushDTO implements MLWorkerWSBaseDTO {
    private PushKind kind;
    @Nullable
    private String key;
    @Nullable
    private String value;
    @JsonProperty("push_title")
    private String pushTitle;

    @JsonProperty("push_details")
    private List<MLWorkerWSPushDetailsDTO> pushDetails;
}
