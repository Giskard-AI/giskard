package ai.giskard.domain.ml;

import ai.giskard.domain.AbstractAuditingEntity;
import ai.giskard.domain.Project;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;

@Entity(name = "slices")
@NoArgsConstructor
@Getter
@Setter
public class Slice extends AbstractAuditingEntity {
    @Id
    @Getter
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @NotNull
    private String name;

    // Later on this will probably depend on the slice type: From a file, from the interface, from the API ?

    @NotNull
    private String code;

    @ManyToOne
    @NotNull
    private Project project;
}
