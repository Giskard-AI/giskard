package ai.giskard.ml.dto;

import lombok.Getter;

@Getter
public class MLWorkerWSPlatformDTO implements MLWorkerWSBaseDTO {
    private String machine;

    private String node;

    private String processor;

    private String release;

    private String system;

    private String version;

}
