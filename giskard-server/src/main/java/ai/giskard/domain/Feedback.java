package ai.giskard.domain;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.Setter;
import org.springframework.data.annotation.CreatedDate;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.Instant;
import java.util.HashSet;
import java.util.Set;

@Getter
@Entity(name = "feedbacks")
public class Feedback extends BaseEntity{
    @Setter
    @ManyToOne
    private Project project;

    @Setter
    @ManyToOne
    private ProjectModel model;

    @Setter
    @ManyToOne
    private Dataset dataset;

    @Setter
    @ManyToOne
    private User user;

    @Setter
    @OneToMany(mappedBy = "feedback", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<FeedbackReply> feedbackReplies = new HashSet<>();

    @Setter
    private String targetFeature;

    @CreatedDate
    @Column(name = "created_on", updatable = false)
    private Instant createdOn = Instant.now();

    @Setter
    @NotNull
    private String feedbackType;

    @Setter
    @Column(columnDefinition = "VARCHAR")
    private String featureName;

    @Setter
    @Column(columnDefinition = "VARCHAR")
    private String featureValue;

    @Setter
    private String feedbackChoice;

    @Setter
    @Column(columnDefinition = "VARCHAR")
    private String feedbackMessage;

    @Setter
    @NotNull
    @Column(columnDefinition = "VARCHAR")
    private String userData;

    @Setter
    @NotNull
    @Column(columnDefinition = "VARCHAR")
    private String originalData;

}
