package ai.giskard.domain;

import ai.giskard.domain.ml.SuiteTest;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.Setter;

import jakarta.persistence.CascadeType;
import jakarta.persistence.DiscriminatorValue;
import jakarta.persistence.Entity;
import jakarta.persistence.OneToMany;
import java.io.Serializable;
import java.util.List;

@Getter
@Entity
@DiscriminatorValue("TEST")
@Setter
public class TestFunction extends Callable implements Serializable {

    @OneToMany(mappedBy = "testFunction", cascade = CascadeType.ALL)
    @JsonIgnore
    private List<SuiteTest> suiteTests;

}
