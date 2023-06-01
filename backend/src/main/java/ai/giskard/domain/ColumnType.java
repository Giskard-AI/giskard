package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import tech.tablesaw.api.ColumnDType;

import java.util.Arrays;
import java.util.Map;
import java.util.stream.Collectors;

public enum ColumnType {
    NUMERIC("numeric"),
    CATEGORY("category"),
    TEXT("text");

    private static final Map<String, ColumnType> BY_NAME = Arrays.stream(ColumnType.values()).collect(Collectors.toMap(ColumnType::getName, columnType -> columnType));
    public static final Map<ColumnType, ColumnDType> featureToColumn= Map.of(NUMERIC, ColumnDType.DOUBLE, CATEGORY, ColumnDType.STRING, TEXT, ColumnDType.TEXT);

    private final String name;

    @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
    public static ColumnType forValue(String name) {
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
    ColumnType(String name) {
        this.name = name;
    }
}
