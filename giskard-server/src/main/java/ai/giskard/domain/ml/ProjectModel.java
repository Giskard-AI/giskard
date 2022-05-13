package ai.giskard.domain.ml;

import ai.giskard.domain.ProjectFile;
import lombok.Getter;
import lombok.NonNull;
import lombok.Setter;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.EnumType;
import javax.persistence.Enumerated;
import java.io.Serializable;


@Entity(name = "project_models")
@Getter
@Setter
public class ProjectModel extends ProjectFile implements Serializable {
    private String name;
    private String languageVersion;
    @Enumerated(EnumType.STRING)
    private ModelLanguage language;
    @Enumerated(EnumType.STRING)
    private ModelType modelType;
    private Float threshold;
    @Column(columnDefinition = "VARCHAR")
    private String features;
    private String target;
    @Column(columnDefinition = "VARCHAR")
    private String classificationLabels;
    @NonNull
    private String requirementsFileName;


}
