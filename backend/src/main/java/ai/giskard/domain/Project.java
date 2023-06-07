package ai.giskard.domain;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.utils.JSONStringAttributeConverter;
import com.fasterxml.jackson.annotation.JsonIdentityInfo;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.ObjectIdGenerators;
import com.fasterxml.jackson.core.type.TypeReference;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.ColumnDefault;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

@Entity(name = "projects")
@NoArgsConstructor
@EntityListeners(AuditingEntityListener.class)
@JsonIdentityInfo(generator = ObjectIdGenerators.PropertyGenerator.class, property = "key")
public class Project extends AbstractAuditingEntity {
    @Id
    @Getter
    @GeneratedValue(strategy = GenerationType.AUTO)
    @JsonIgnore
    private Long id;

    @Converter
    public static class InspectionSettingsConverter extends JSONStringAttributeConverter<InspectionSettings> {
        @Override
        public TypeReference<InspectionSettings> getValueTypeRef() {
            return new TypeReference<>() {
            };
        }

        @Override
        public InspectionSettings nullConverter() {
            return new InspectionSettings();
        }
    }

    @Getter
    @Setter
    @NotNull
    @Column(unique = true, nullable = false)
    private String key;

    @Getter
    @Setter
    @NotNull
    private String name;

    @Getter
    @Setter
    private String description;

    @Getter
    @Setter
    @JsonIgnore
    @ManyToOne(fetch = FetchType.EAGER)
    private User owner;

    @Getter
    @Setter
    @OneToMany(mappedBy = "project", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<ProjectModel> models = new HashSet<>();


    @Getter
    @Setter
    @JsonIgnore
    @OneToMany(mappedBy = "project", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    private Set<Dataset> datasets = new HashSet<>();

    @Getter
    @JsonIgnore
    @OneToMany(mappedBy = "project", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    private final Set<Feedback> feedbacks = new HashSet<>();

    @Getter
    @JsonIgnore
    @OneToMany(mappedBy = "project", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    private final Set<TestSuite> testSuites = new HashSet<>();

    @Getter
    @Setter
    @ManyToMany(fetch = FetchType.EAGER, cascade = CascadeType.ALL)
    @JsonProperty(value = "guestlist")
    @JoinTable(
        name = "projects_guests",
        joinColumns = @JoinColumn(name = "project_id"),
        inverseJoinColumns = @JoinColumn(name = "user_id"))
    private Set<User> guests = new HashSet<>();


    @Getter
    @Setter
    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = InspectionSettingsConverter.class)
    private InspectionSettings inspectionSettings;


    @Setter
    @Getter
    @NotNull
    @Enumerated(EnumType.STRING)
    @ColumnDefault(value = "EXTERNAL")
    private MLWorkerType mlWorkerType = MLWorkerType.EXTERNAL;

    public boolean isUsingInternalWorker() {
        return mlWorkerType == MLWorkerType.INTERNAL;
    }

    public void addGuest(User user) {
        this.guests.add(user);
    }

    public void removeGuest(User user) {
        this.guests.remove(user);
        user.getProjects().remove(this);
    }

    public Project(String key, String name, String description, User owner) {
        this.key = key;
        this.name = name;
        this.description = description;
        this.owner = owner;
        this.inspectionSettings = new InspectionSettings();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Project project = (Project) o;
        return getKey().equals(project.getKey());
    }

    @Override
    public int hashCode() {
        return Objects.hash(getKey());
    }
}
