package ai.giskard.web.dto;

import ai.giskard.domain.ColumnType;
import lombok.AllArgsConstructor;

@AllArgsConstructor
public enum NoCodeSlicingType {

    IS(ColumnType.values()),
    IS_NOT(ColumnType.values()),
    CONTAINS(new ColumnType[]{ColumnType.TEXT}),
    DOES_NOT_CONTAINS(new ColumnType[]{ColumnType.TEXT}),
    STARTS_WITH(new ColumnType[]{ColumnType.TEXT}),
    ENDS_WITH(new ColumnType[]{ColumnType.TEXT}),
    IS_EMPTY(ColumnType.values()),
    IS_NOT_EMPTY(ColumnType.values());


    private final ColumnType[] allowed_types;


}
