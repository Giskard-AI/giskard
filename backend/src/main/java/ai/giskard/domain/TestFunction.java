package ai.giskard.domain;

import ai.giskard.domain.ml.SuiteTest;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import org.apache.commons.lang3.builder.EqualsBuilder;

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
    @Column
    private String debugDescription;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;

        if (!(o instanceof TestFunction testFunction)) return false;

        return new EqualsBuilder().append(getUuid(), testFunction.getUuid()).isEquals();
    }

    @Override
    public int hashCode() {
        return super.hashCode();
    }
}
