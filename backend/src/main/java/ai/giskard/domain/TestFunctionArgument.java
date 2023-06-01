package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;

@Getter
@Entity(name = "test_function_arguments")
@Table(uniqueConstraints={
    @UniqueConstraint(columnNames = {"test_function_uuid", "name"})
})
@Setter
public class TestFunctionArgument extends BaseEntity {

    @ManyToOne
    @JoinColumn(name = "test_function_uuid")
    private TestFunction testFunction;
    @Column(nullable = false)
    private String name;
    @Column(nullable = false)
    private String type;
    private boolean optional;
    private String defaultValue;

}
