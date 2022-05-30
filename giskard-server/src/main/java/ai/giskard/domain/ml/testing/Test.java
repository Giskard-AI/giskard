package ai.giskard.domain.ml.testing;

import ai.giskard.domain.AbstractAuditingEntity;
import ai.giskard.domain.ml.CodeLanguage;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.TestType;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.*;

import javax.persistence.*;
import java.util.HashSet;
import java.util.Set;


@Entity
@Builder
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class Test extends AbstractAuditingEntity {
    private String name;

    @Column(columnDefinition = "VARCHAR")
    private String code;

    private CodeLanguage language;

    @ManyToOne
    private TestSuite testSuite;

    @Enumerated(EnumType.STRING)
    private TestType type;

    @OneToMany(mappedBy = "test", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<TestExecution> testExecutions = new HashSet<>();

}
