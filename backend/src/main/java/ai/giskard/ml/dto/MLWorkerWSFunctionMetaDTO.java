package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSFunctionMetaDTO implements MLWorkerWSBaseDTO {
    String uuid;

    String name;

    String displayName;

    Integer version;

    String module;

    String doc;

    String moduleDoc;

    List<MLWorkerWSFunctionMetaDTO> args;

    List<String> tags;

    String code;

    String type;
}
