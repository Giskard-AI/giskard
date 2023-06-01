package ai.giskard.utils;

import ai.giskard.domain.FeatureType;
import ai.giskard.domain.ml.Dataset;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.List;
import java.util.Map;

import static ai.giskard.domain.FeatureType.CATEGORY;
import static ai.giskard.domain.FeatureType.NUMERIC;
import static org.junit.jupiter.api.Assertions.assertEquals;

class JSONStringAttributeConvertersTest {

    @Test
    void FeatureTypesConverterDeserializeTest() {
        Dataset.FeatureTypesConverter converter = new Dataset.FeatureTypesConverter();
        Map<String, FeatureType> map = Map.of("category_key", CATEGORY, "numeric_key", NUMERIC);
        String serialized = converter.convertToDatabaseColumn(map);

        assertEquals(map, converter.convertToEntityAttribute(serialized));
    }

    @Test
    void SimpleJSONStringAttributeConverterMapTest() {
        SimpleJSONStringAttributeConverter converter = new SimpleJSONStringAttributeConverter();
        Map<String, Object> map = Map.of(
            "number", 1,
            "string", "string",
            "boolean", true,
            "list", Arrays.asList(1, 2, 3)
        );
        String serialized = converter.convertToDatabaseColumn(map);
        Object obj = converter.convertToEntityAttribute(serialized);

        assertEquals(map, obj);
    }

    @Test
    void SimpleJSONStringAttributeConverterListTest() {
        SimpleJSONStringAttributeConverter converter = new SimpleJSONStringAttributeConverter();
        List<Object> list = Arrays.asList(
            1,
            "string",
            true,
            Arrays.asList(1, 2, 3)
        );
        String serialized = converter.convertToDatabaseColumn(list);
        Object obj = converter.convertToEntityAttribute(serialized);

        assertEquals(list, obj);
    }

}
