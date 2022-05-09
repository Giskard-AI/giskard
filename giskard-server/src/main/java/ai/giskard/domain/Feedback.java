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
import org.springframework.data.annotation.CreatedDate;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.Instant;
import java.util.HashSet;
import java.util.Set;

@Getter
@Entity(name = "feedbacks")
@TypeDefs({
    @TypeDef(name = "json", typeClass = JsonStringType.class),
    @TypeDef(name = "jsonb", typeClass = JsonBinaryType.class)
})
public class Feedback {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

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
    private String featureName;
    @Setter
    private String featureValue;
    @Setter
    private String feedbackChoice;
    @Setter
    private String feedbackMessage;
    @Setter
    @NotNull
    @Type(type = "jsonb")
    @Column(columnDefinition = "jsonb")
    private String userData;
    @Setter
    @NotNull
    @Type(type = "jsonb")
    @Column(columnDefinition = "jsonb")
    private String originalData;
}
