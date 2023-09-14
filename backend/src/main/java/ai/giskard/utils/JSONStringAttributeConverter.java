package ai.giskard.utils;

import com.fasterxml.jackson.core.type.TypeReference;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

@Converter
public abstract class JSONStringAttributeConverter<T> implements AttributeConverter<T, String> {
    @Override
    public final String convertToDatabaseColumn(Object attribute) {
        return JSON.toJSON(attribute);
    }

    @Override
    public final T convertToEntityAttribute(String dbData) {
        if (dbData == null) {
            return nullConverter();
        }
        return JSON.fromJSON(dbData, getValueTypeRef());
    }

    /**
     * @return a default object value in case there's null stored in the database
     */
    public T nullConverter() {
        return null;
    }

    public abstract TypeReference<T> getValueTypeRef();
}
