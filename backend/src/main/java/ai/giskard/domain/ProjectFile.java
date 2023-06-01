package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonBackReference;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.Index;
import javax.persistence.ManyToOne;
import javax.persistence.MappedSuperclass;
import javax.persistence.Table;


@MappedSuperclass
@Table(indexes = @Index(columnList = "fileName"))
@NoArgsConstructor
@Getter
@Setter
public abstract class ProjectFile extends AbstractAuditingEntity {
    private String fileName;

    @ManyToOne
    @JsonBackReference
    private Project project;

    private long size;
}
