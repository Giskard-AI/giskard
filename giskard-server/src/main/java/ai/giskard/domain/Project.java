package ai.giskard.domain;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import com.fasterxml.jackson.annotation.JsonIdentityInfo;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.ObjectIdGenerators;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;

@Entity(name = "projects")
@NoArgsConstructor
@EntityListeners(AuditingEntityListener.class)
@JsonIdentityInfo(generator = ObjectIdGenerators.PropertyGenerator.class, property = "id")
public class Project {
    @Getter
    @Setter
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @Getter
    @Setter
    @NotNull
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
    @CreatedDate
    @Column(name = "created_on", updatable = false)
    private LocalDateTime createdOn;

    @Getter
    @Setter
    @ManyToOne(fetch = FetchType.EAGER)
    private User owner;

    @Getter
    @Setter
    @OneToMany(mappedBy = "project", fetch = FetchType.LAZY)
    @JsonIgnore
    private Set<ProjectModel> models = new HashSet<ProjectModel>();


    @Getter
    @Setter
    @OneToMany(mappedBy = "project", fetch = FetchType.LAZY)
    private Set<Dataset> datasets = new HashSet<Dataset>();


    @Getter
    @Setter
    @ManyToMany(fetch = FetchType.EAGER, cascade = CascadeType.ALL)
    @JsonProperty(value = "guestlist")
    @JoinTable(
        name = "projects_guests",
        joinColumns = @JoinColumn(name = "project_id"),
        inverseJoinColumns = @JoinColumn(name = "user_id"))
    private Set<User> guests = new HashSet<>();


    public void addGuest(User user) {
        this.guests.add(user);
        //user.getProjects().add(this);
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
    }

    //    class Project(Base):
//    __tablename__ = "projects"
//
    //    id = Column(Integer, primary_key=True, index=True)
    //    key = Column(String, index=True, unique=True, nullable=False)
    //    name = Column(String, nullable=False)
    //    description = Column(String)
//    created_on = Column(DateTime(timezone=True), default=datetime.datetime.now)
//    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
//    owner_details = relationship("User")
//    guest_list = relationship("User", secondary=association_table)
//    model_files = relationship("ProjectModel", cascade="all, delete")
//    data_files = relationship("Dataset", cascade="all, delete")

}
