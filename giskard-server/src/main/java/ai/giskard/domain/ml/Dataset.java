package ai.giskard.domain.ml;


import ai.giskard.domain.FeatureType;
import ai.giskard.domain.ProjectFile;
import ai.giskard.utils.JSONStringAttributeConverter;
import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.core.type.TypeReference;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

@Entity(name = "datasets")
@NoArgsConstructor
@Getter
public class Dataset extends ProjectFile {
    @Converter
    public static class FeatureTypesConverter extends JSONStringAttributeConverter<Map<String, FeatureType>> {
        @Override
        public TypeReference<Map<String, FeatureType>> getValueTypeRef() {return new TypeReference<>() {};}
    }

    @Setter
    private String name;

    @Column(columnDefinition = "VARCHAR")
    @Setter
    @Convert(converter = FeatureTypesConverter.class)
    private Map<String, FeatureType> featureTypes;

    @Setter
    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private Map<String, String> columnTypes;
    @Setter
    private String target;

    @Setter
    @OneToMany(mappedBy = "dataset", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<Inspection> inspections = new HashSet<>();

    public boolean hasTarget(){
        return getTarget() != null;
    }

}
