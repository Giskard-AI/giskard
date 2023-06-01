package ai.giskard.domain.ml;


import ai.giskard.domain.AbstractAuditingEntity;
import ai.giskard.domain.FeatureType;
import ai.giskard.domain.Project;
import ai.giskard.utils.JSONStringAttributeConverter;
import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import com.fasterxml.jackson.annotation.JsonBackReference;
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
@Setter
public class Dataset extends AbstractAuditingEntity {
    @Id
    @Column(length = 32)
    private String id;

    @Converter
    public static class FeatureTypesConverter extends JSONStringAttributeConverter<Map<String, FeatureType>> {
        @Override
        public TypeReference<Map<String, FeatureType>> getValueTypeRef() {
            return new TypeReference<>() {
            };
        }
    }

    private String name;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = FeatureTypesConverter.class)
    private Map<String, FeatureType> featureTypes;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private Map<String, String> columnTypes;
    private String target;

    @OneToMany(mappedBy = "dataset", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<Inspection> inspections = new HashSet<>();

    @ManyToOne
    @JsonBackReference
    private Project project;

    private Long originalSizeBytes;

    private Long compressedSizeBytes;
}
