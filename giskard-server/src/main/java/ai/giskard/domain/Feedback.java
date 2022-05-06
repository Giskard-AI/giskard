package ai.giskard.domain;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.vladmihalcea.hibernate.type.json.JsonBinaryType;
import com.vladmihalcea.hibernate.type.json.JsonStringType;
import lombok.Getter;
import lombok.Setter;
import org.hibernate.annotations.Type;
import org.hibernate.annotations.TypeDef;
import org.hibernate.annotations.TypeDefs;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;

@Entity(name="feedbacks")
@TypeDefs({
    @TypeDef(name = "json", typeClass = JsonStringType.class),
    @TypeDef(name = "jsonb", typeClass = JsonBinaryType.class)
})
public class Feedback {
    @Getter
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

    @Getter
    @Setter
    @OneToMany(mappedBy = "feedback", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<FeedbackReply> feedbackReplies = new HashSet<>();


    private String targetFeature;

    private LocalDateTime createdOn;
    @NotNull
    private String feedbackType;
    private String featureName;
    private String featureValue;
    private String feedbackChoice;
    private String feedbackMessage;
    @NotNull
    @Type(type = "jsonb")
    @Column(columnDefinition = "jsonb")
    private String userData;
    @NotNull
    @Type(type = "jsonb")
    @Column(columnDefinition = "jsonb")
    private String originalData;
}
