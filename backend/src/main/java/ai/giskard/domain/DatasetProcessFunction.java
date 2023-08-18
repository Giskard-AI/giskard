package ai.giskard.domain;

import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import ai.giskard.web.dto.DatasetProcessFunctionType;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

import java.util.List;
import java.util.Map;

@Getter
@Setter
@MappedSuperclass
public abstract class DatasetProcessFunction extends Callable {
    @Column
    private String projectKey;
    @Column(nullable = false)
    private boolean cellLevel;
    @Column
    private String columnType;
    @Column
    @Enumerated(EnumType.STRING)
    private DatasetProcessFunctionType processType;
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private List<Map<String, Object>> clauses; // NOSONAR
}
