package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.*;

import jakarta.persistence.*;

@Getter
@Entity(name = "test_function_arguments")
@Table(uniqueConstraints = {
    @UniqueConstraint(columnNames = {"function_uuid", "name"})
})
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FunctionArgument extends BaseEntity {

    @ManyToOne
    @JoinColumn(name = "function_uuid")
    @JsonIgnore
    private Callable function;
    @Column(nullable = false)
    private String name;
    @Column(nullable = false)
    private String type;
    private boolean optional;
    private String defaultValue;
    private int argOrder;

}
