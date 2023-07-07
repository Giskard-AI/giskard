package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.Setter;

@Getter
@Setter
public class MLWorkerWSGetInfoParamDTO implements MLWorkerWSBaseDTO {
    @JsonProperty("list_packages")
    private boolean listPackages;
}
