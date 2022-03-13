package ai.giskard.domain;

import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.LocalDateTime;

@MappedSuperclass
@Table(indexes = @Index(columnList = "fileName"))
public abstract class ProjectFile {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    private String fileName;

    @NotNull
    private String location;

    private LocalDateTime createdOn;

    @Getter
    @Setter
    @ManyToOne
    private User owner;

    @Getter
    @Setter
    @ManyToOne
    private Project project;
}
