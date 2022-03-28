package ai.giskard.domain;

import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.LocalDateTime;

@MappedSuperclass
@Table(indexes = @Index(columnList = "fileName"))
public abstract class ProjectFile {
    @Getter
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @Getter
    private String fileName;

    @NotNull
    @Getter
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
