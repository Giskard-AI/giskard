package ai.giskard.domain.ml.testing;

import ai.giskard.domain.AbstractAuditingEntity;
import ai.giskard.domain.ml.CodeLanguage;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.TestType;
import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;

@Entity
public class Test extends AbstractAuditingEntity {
    @Setter
    @Getter
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(name = "id", nullable = false)
    private Long id;

    @Getter
    @Setter
    private String name;

    @Getter
    @Setter
    @Lob
    private String code;

    @Getter
    @Setter
    private CodeLanguage language;

    @Getter
    @Setter
    @ManyToOne
    private TestSuite testSuite;

    @Getter @Setter
    @Enumerated(EnumType.STRING)
    private TestType type;
}
