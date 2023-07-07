package ai.giskard.domain;

import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import ai.giskard.web.dto.DatasetProcessFunctionType;
import lombok.Getter;
import lombok.Setter;

import javax.persistence.Column;
import javax.persistence.Convert;
import javax.persistence.MappedSuperclass;
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
    @Column()
    private DatasetProcessFunctionType processType;
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private List<Map<String, Object>> clauses; // NOSONAR
}
