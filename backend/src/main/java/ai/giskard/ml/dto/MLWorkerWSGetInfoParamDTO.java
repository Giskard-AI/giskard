package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class MLWorkerWSGetInfoParamDTO implements MLWorkerWSBaseDTO {
    @JsonProperty("list_packages")
    private boolean listPackages;
}
