package ai.giskard.repository.ml;

import ai.giskard.domain.DatasetProcessFunction;
import ai.giskard.domain.Project;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.NoRepositoryBean;

import java.util.List;

@NoRepositoryBean
public interface DatasetProcessFunctionRepository<E extends DatasetProcessFunction> extends CallableRepository<E> {

    @Query("SELECT e FROM #{#entityName} e LEFT JOIN e.projects p WHERE p IS NULL OR p = :project")
    List<E> findAllForProject(Project project);
}
