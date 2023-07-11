package ai.giskard.ml.dto;

import java.util.List;

public class MLWorkerWSDatasetProcessFunctionMetaDTO implements MLWorkerWSBaseDTO {
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

    Boolean cellLevel;

    String columnType;

    String processType;
}
