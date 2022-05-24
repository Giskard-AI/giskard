package ai.giskard.utils;

import com.fasterxml.jackson.core.type.TypeReference;

public class SimpleJSONStringAttributeConverter extends JSONStringAttributeConverter<Object> {
    @Override
    public TypeReference<Object> getValueTypeRef() {
        return new TypeReference<>() {
        };
    }
}
