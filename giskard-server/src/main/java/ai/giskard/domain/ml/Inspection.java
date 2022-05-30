package ai.giskard.domain.ml;


import ai.giskard.domain.BaseEntity;
import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;

@Getter
@Setter
@Entity(name = "inspections")
public class Inspection extends BaseEntity {
    @ManyToOne
    private Dataset dataset;

    @ManyToOne
    private ProjectModel model;


}
