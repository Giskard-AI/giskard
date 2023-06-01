package ai.giskard.domain;

import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;

@Getter
@Entity(name = "test_function_arguments")
@Table(uniqueConstraints = {
    @UniqueConstraint(columnNames = {"function_uuid", "name"})
})
@Setter
public class FunctionArgument extends BaseEntity {

    @ManyToOne
    @JoinColumn(name = "function_uuid")
    private Callable function;
    @Column(nullable = false)
    private String name;
    @Column(nullable = false)
    private String type;
    private boolean optional;
    private String defaultValue;
    private int argOrder;

}
