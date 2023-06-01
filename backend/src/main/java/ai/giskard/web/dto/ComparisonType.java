package ai.giskard.web.dto;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
@Getter
public enum ComparisonType {
    IS(true, "==", "giskard.slicing.slice.EqualTo(%s, %s)"),
    IS_NOT(true, "!=", "giskard.slicing.slice.NotEqualTo(%s, %s)"),
    CONTAINS(true, "contains", "giskard.slicing.slice.ContainsWord(%s, %s, is_not=False)"),
    DOES_NOT_CONTAINS(true, "does not contain", "giskard.slicing.slice.ContainsWord(%s, %s, is_not=True)"),
    STARTS_WITH(true, "startswith", "giskard.slicing.slice.StartsWith(%s, %s)"),
    ENDS_WITH(true, "endswith", "giskard.slicing.slice.EndsWith(%s, %s)"),
    IS_EMPTY(false, "is empty", "giskard.slicing.slice.IsNa(%s, is_not=True)"),
    IS_NOT_EMPTY(false, "is not empty", "giskard.slicing.slice.IsNa(%s, is_not=False)");

    private final boolean valueRequired;
    private final String symbol;
    private final String codeTemplate;

}
