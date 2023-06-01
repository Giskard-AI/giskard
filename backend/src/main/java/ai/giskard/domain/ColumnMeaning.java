package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import tech.tablesaw.api.ColumnType;

import java.util.Arrays;
import java.util.Map;
import java.util.stream.Collectors;

public enum ColumnMeaning {
    NUMERIC("numeric"),
    CATEGORY("category"),
    TEXT("text");

    private static final Map<String, ColumnMeaning> BY_NAME = Arrays.stream(ColumnMeaning.values()).collect(Collectors.toMap(ColumnMeaning::getName, columnMeaning -> columnMeaning));
    public static final Map<ColumnMeaning, ColumnType> featureToColumn= Map.of(NUMERIC, ColumnType.DOUBLE, CATEGORY, ColumnType.STRING, TEXT, ColumnType.TEXT);

    private final String name;

    @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
    public static ColumnMeaning forValue(String name) {
        String cleanName = name.trim().toLowerCase();
        if (!BY_NAME.containsKey(cleanName)) {
            String join = String.join(",", BY_NAME.keySet());
            throw new IllegalArgumentException(String.format("invalid feature type: %s, supported values: %s", cleanName, join));
        }
        return BY_NAME.get(cleanName);
    }

    @JsonValue
    public String getName() {
        return name;
    }
    ColumnMeaning(String name) {
        this.name = name;
    }
}
