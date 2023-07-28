package ai.giskard.domain.ml;

import ai.giskard.domain.AbstractAuditingEntity;
import ai.giskard.domain.Project;
import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import java.io.Serial;
import java.util.List;
import java.util.Set;
import java.util.UUID;


@Entity(name = "project_models")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ProjectModel extends AbstractAuditingEntity {
    @Serial
    private static final long serialVersionUID = 0L;

    @Id
    private UUID id;
    private String name;

    @ManyToMany(mappedBy = "models")
    @JsonIgnore
    private Set<Project> projects;

    private long size;

    private String languageVersion;

    @Enumerated(EnumType.STRING)
    private ModelLanguage language;

    @Enumerated(EnumType.STRING)
    private ModelType modelType;

    private Float threshold;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private List<String> featureNames;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private List<String> classificationLabels;

    private String classificationLabelsDtype;
}
