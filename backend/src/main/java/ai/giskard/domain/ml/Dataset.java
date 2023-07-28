package ai.giskard.domain.ml;


import ai.giskard.domain.AbstractAuditingEntity;
import ai.giskard.domain.ColumnType;
import ai.giskard.domain.Project;
import ai.giskard.utils.JSONStringAttributeConverter;
import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.core.type.TypeReference;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import java.io.Serial;
import java.util.*;

@Entity(name = "datasets")
@NoArgsConstructor
@Getter
@Setter
public class Dataset extends AbstractAuditingEntity {
    @Serial
    private static final long serialVersionUID = 0L;
    @Id
    private UUID id;

    @Converter
    public static class ColumnTypesConverter extends JSONStringAttributeConverter<Map<String, ColumnType>> {
        @Override
        public TypeReference<Map<String, ColumnType>> getValueTypeRef() {
            return new TypeReference<>() {
            };
        }
    }

    private String name;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = ColumnTypesConverter.class)
    private Map<String, ColumnType> columnTypes;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private Map<String, String> columnDtypes;
    private String target;

    @OneToMany(mappedBy = "dataset", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<Inspection> inspections = new HashSet<>();

    @ManyToMany(mappedBy = "datasets")
    @JsonIgnore
    private List<Project> projects;

    private Long originalSizeBytes;

    private Long compressedSizeBytes;

    private long numberOfRows;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private Map<String, List<String>> categoryFeatures;

}
