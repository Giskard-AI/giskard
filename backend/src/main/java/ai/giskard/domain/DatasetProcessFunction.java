package ai.giskard.domain;

import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import ai.giskard.web.dto.DatasetProcessFunctionType;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import org.hibernate.annotations.ColumnDefault;

import java.util.List;
import java.util.Map;
import java.util.Set;

@Getter
@Setter
@MappedSuperclass
public abstract class DatasetProcessFunction extends Callable {

    @ManyToMany
    @JoinTable(
        name = "dataset_process_function_projects",
        joinColumns = {@JoinColumn(name = "function_uuid")},
        inverseJoinColumns = {@JoinColumn(name = "project_id")}
    )
    private Set<Project> projects;

    @Column(nullable = false)
    @ColumnDefault("false")
    private boolean cellLevel;
    @Column
    private String columnType;
    @Column
    @Enumerated(EnumType.STRING)
    private DatasetProcessFunctionType processType;
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private List<Map<String, Object>> clauses; // NOSONAR
}

