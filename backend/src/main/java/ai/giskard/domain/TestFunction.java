package ai.giskard.domain;

import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;
import java.io.Serializable;
import java.util.List;

@Getter
@Entity(name = "test_functions")
@Table(uniqueConstraints = {
    @UniqueConstraint(columnNames = {"name", "module", "version"})
})
@Setter
public class TestFunction extends Callable implements Serializable {

    @OneToMany(mappedBy = "testFunction", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<TestFunctionArgument> args;


}
