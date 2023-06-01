package ai.giskard.domain.ml;

import ai.giskard.domain.ProjectFile;
import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.NonNull;
import lombok.Setter;

import javax.persistence.*;
import java.util.List;


@Entity(name = "project_models")
@Getter
@Setter
@NoArgsConstructor
public class ProjectModel extends ProjectFile {
    private String name;

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

    @NonNull
    private String requirementsFileName;
}
