package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonBackReference;
import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.io.Serializable;
import java.time.LocalDateTime;


@MappedSuperclass
@Table(indexes = @Index(columnList = "fileName"))
public abstract class ProjectFile implements Serializable {
    @Getter
    @Setter
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @Getter
    private String fileName;

    @NotNull
    @Getter
    private String location;

    @Getter
    private LocalDateTime createdOn;

    @Getter
    @Setter
    @ManyToOne
    private User owner;

    @Getter
    @Setter
    @ManyToOne
    @JsonBackReference
    private Project project;
}
