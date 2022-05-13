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
public abstract class ProjectFile extends AbstractAuditingEntity implements Serializable {
    @Getter
    @Setter
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @Getter
    @Setter
    private String fileName;

    @Getter
    @Setter
    @ManyToOne
    @JsonBackReference
    private Project project;
}
