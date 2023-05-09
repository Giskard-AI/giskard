package ai.giskard.domain.ml;

import ai.giskard.worker.GeneratedTestInput;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "test_input")
@Getter
@Setter
@NoArgsConstructor
public class FunctionInput implements Serializable {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(name = "id", nullable = false)
    private Long id;

    @NotNull
    private String name;

    private String type;

    @Column(columnDefinition = "CLOB")
    private String value;

    private boolean isAlias = false;

    @OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
    @JoinColumn(name = "function_input_id")
    private List<FunctionInput> params = new ArrayList<>();

    public FunctionInput(GeneratedTestInput testInput) {
        this.name = testInput.getName();
        this.value = testInput.getValue();
        this.isAlias = testInput.getIsAlias();
    }
}
