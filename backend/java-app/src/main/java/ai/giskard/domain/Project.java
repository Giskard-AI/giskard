package ai.giskard.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.validation.constraints.NotNull;
import java.time.LocalDateTime;

@Entity(name = "projects")
@NoArgsConstructor
public class Project {
    @Getter
    @Setter
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @NotNull
    private String key;
    @NotNull
    private String name;
    private String description;
    private LocalDateTime localDateTime;

    public Project(String key, String name, String description, LocalDateTime localDateTime) {
        this.key = key;
        this.name = name;
        this.description = description;
        this.localDateTime = localDateTime;
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
