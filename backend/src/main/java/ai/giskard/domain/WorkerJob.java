package ai.giskard.domain;

import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.util.Date;

@Getter
@Setter
@MappedSuperclass
@Inheritance(strategy = InheritanceType.TABLE_PER_CLASS)
public abstract class WorkerJob extends BaseEntity {

    private Date executionDate = new Date();
    private Date completionDate;
    
    @NotNull
    @Enumerated(EnumType.STRING)
    private MLWorkerType mlWorkerType;

}
