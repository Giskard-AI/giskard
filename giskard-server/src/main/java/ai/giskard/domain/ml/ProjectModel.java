package ai.giskard.domain.ml;

import ai.giskard.domain.ProjectFile;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.NonNull;
import lombok.Setter;

import javax.persistence.CascadeType;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.FetchType;
import javax.persistence.OneToMany;
import javax.persistence.EnumType;
import javax.persistence.Enumerated;
import java.io.Serializable;
import java.util.HashSet;
import java.util.Set;


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

    @OneToMany(mappedBy = "model", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<Inspection> inspections = new HashSet<>();
}
