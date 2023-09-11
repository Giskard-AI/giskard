package ai.giskard.domain;

import ai.giskard.domain.ml.SuiteTest;
import lombok.Getter;
import lombok.Setter;

import jakarta.persistence.*;
import java.io.Serializable;
import java.util.List;

@Getter
@Entity
@DiscriminatorValue("TEST")
@Setter
public class TestFunction extends Callable implements Serializable {

    @OneToMany(mappedBy = "testFunction", cascade = CascadeType.ALL)
    private List<SuiteTest> suiteTests;
    @Column
    private String debugDescription;

}
