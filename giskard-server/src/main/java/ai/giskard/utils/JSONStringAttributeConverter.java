package ai.giskard.utils;

import com.fasterxml.jackson.core.type.TypeReference;

import javax.persistence.AttributeConverter;
import javax.persistence.Converter;

@Converter
public abstract class JSONStringAttributeConverter<T> implements AttributeConverter<T, String> {
    @Override
    public final String convertToDatabaseColumn(Object attribute) {
        return JSON.toJSON(attribute);
    }

    @Override
    public final T convertToEntityAttribute(String dbData) {
        return JSON.fromJSON(dbData, getValueTypeRef());
    }

    public abstract TypeReference<T> getValueTypeRef();
}
