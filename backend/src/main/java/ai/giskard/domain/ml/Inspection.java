package ai.giskard.domain.ml;


import ai.giskard.domain.AbstractAuditingEntity;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.Setter;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.ManyToOne;
import java.io.Serial;

@Getter
@Setter
@Entity(name = "inspections")
public class Inspection extends AbstractAuditingEntity {
    @Serial
    private static final long serialVersionUID = 0L;

    @Id
    @JsonIgnore
    @GeneratedValue
    private Long id;

    private String name;

    @ManyToOne
    private Dataset dataset;

    @ManyToOne
    private ProjectModel model;

    private boolean sample;
}
