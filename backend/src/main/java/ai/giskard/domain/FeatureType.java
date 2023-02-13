package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import tech.tablesaw.api.ColumnType;

import java.util.Arrays;
import java.util.Map;
import java.util.stream.Collectors;

public enum FeatureType {
    NUMERIC("numeric"),
    CATEGORY("category"),
    TEXT("text");

    private static final Map<String, FeatureType> BY_NAME = Arrays.stream(FeatureType.values()).collect(Collectors.toMap(FeatureType::getName, featureType -> featureType));
    public static final Map<FeatureType, ColumnType> featureToColumn= Map.of(NUMERIC, ColumnType.DOUBLE, CATEGORY, ColumnType.STRING, TEXT, ColumnType.TEXT);

    private final String name;

    @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
    public static FeatureType forValue(String name) {
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
    FeatureType(String name) {
        this.name = name;
    }
}
