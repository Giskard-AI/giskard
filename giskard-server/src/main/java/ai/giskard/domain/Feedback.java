package ai.giskard.domain;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.LocalDateTime;

@Entity
public class Feedback {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @Getter
    @Setter
    @ManyToOne
    private Project project;

    @Getter
    @Setter
    @ManyToOne
    private ProjectModel model;

    @Getter
    @Setter
    @ManyToOne
    private Dataset dataset;

    @Getter
    @Setter
    @ManyToOne
    private User user;

    private String targetFeature;

    private LocalDateTime createdOn;
    @NotNull
    private String feedbackType;
    private String featureName;
    private String featureValue;
    private String feedbackChoice;
    private String feedbackMessage;
    @NotNull
    private String userData;
    @NotNull
    private String originalData;
}
