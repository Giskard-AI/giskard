package ai.giskard.web.dto;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
@Getter
public enum ComparisonType {
    IS(true, "=="),
    IS_NOT(true, "!="),
    CONTAINS(true, "contains"),
    DOES_NOT_CONTAINS(true, "does not contain"),
    STARTS_WITH(true, "startswith"),
    ENDS_WITH(true, "endswith"),
    IS_EMPTY(false, "is empty"),
    IS_NOT_EMPTY(false, "is not empty");

    private final boolean valueRequired;
    private final String symbol;

}
