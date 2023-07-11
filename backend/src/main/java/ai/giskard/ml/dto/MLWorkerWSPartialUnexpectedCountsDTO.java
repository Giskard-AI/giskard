package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSPartialUnexpectedCountsDTO {
    private List<Integer> value;

    private Integer count;
}
