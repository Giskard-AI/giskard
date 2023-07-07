package ai.giskard.ml.dto;

import lombok.Getter;

@Getter
public class MLWorkerWSPlatformDTO implements MLWorkerWSBaseDTO {
    public String machine;

    public String node;

    public String processor;

    public String release;

    public String system;

    public String version;

}
