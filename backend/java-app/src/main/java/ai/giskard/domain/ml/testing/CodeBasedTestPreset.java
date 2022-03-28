package ai.giskard.domain.ml.testing;

import ai.giskard.domain.AbstractAuditingEntity;
import ai.giskard.domain.ml.CodeLanguage;
import ai.giskard.service.dto.ml.CodeBasedTestPresetDTO;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;

@Entity
@NoArgsConstructor
public class CodeBasedTestPreset extends AbstractAuditingEntity {
    @lombok.Setter
    @lombok.Getter
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(name = "id", nullable = false)
    private Long id;

    @Getter
    @Setter
    private String name;

    @Getter
    @Setter
    private String code;

    @Getter
    @Setter
    @Enumerated(EnumType.STRING)
    private CodeLanguage language;

    public CodeBasedTestPreset(String name, String code, CodeLanguage language) {
        this.name = name;
        this.code = code;
        this.language = language;
    }

    public CodeBasedTestPreset(CodeBasedTestPresetDTO dto) {
        this.id = dto.getId();
        this.name = dto.getName();
        this.code = dto.getCode();
        this.language = dto.getLanguage();
    }
}
