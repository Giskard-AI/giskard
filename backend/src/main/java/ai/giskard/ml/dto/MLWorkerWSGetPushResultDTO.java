package ai.giskard.ml.dto;

import lombok.Getter;
import lombok.Setter;

import javax.annotation.Nullable;

@Getter
@Setter
public class MLWorkerWSGetPushResultDTO implements MLWorkerWSBaseDTO {
    @Nullable
    private MLWorkerWSPushDTO perturbation;
    @Nullable
    private MLWorkerWSPushDTO contribution;
    @Nullable
    private MLWorkerWSPushDTO borderline;
    @Nullable
    private MLWorkerWSPushDTO overconfidence;
    @Nullable
    private MLWorkerWSPushActionDTO action;
}
