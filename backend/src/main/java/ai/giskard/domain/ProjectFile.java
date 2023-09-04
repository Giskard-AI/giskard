package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonBackReference;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.persistence.*;
import java.io.Serial;


@MappedSuperclass
@Table(indexes = @Index(columnList = "fileName"))
@NoArgsConstructor
@Getter
@Setter
public abstract class ProjectFile extends AbstractAuditingEntity {
    @Serial
    private static final long serialVersionUID = 0L;
    @Id
    @GeneratedValue
    private Long id;
    private String fileName;

    @ManyToOne
    @JsonBackReference
    private Project project;

    private long size;
}
