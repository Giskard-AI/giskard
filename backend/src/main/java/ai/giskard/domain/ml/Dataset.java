package ai.giskard.domain.ml;


import ai.giskard.domain.AbstractAuditingEntity;
import ai.giskard.domain.ColumnMeaning;
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
import java.util.UUID;

@Entity(name = "datasets")
@NoArgsConstructor
@Getter
@Setter
public class Dataset extends AbstractAuditingEntity {
    @Id
    private UUID id;

    @Converter
    public static class ColumnMeaningsConverter extends JSONStringAttributeConverter<Map<String, ColumnMeaning>> {
        @Override
        public TypeReference<Map<String, ColumnMeaning>> getValueTypeRef() {
            return new TypeReference<>() {
            };
        }
    }

    private String name;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = ColumnMeaningsConverter.class)
    private Map<String, ColumnMeaning> columnMeanings;

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
