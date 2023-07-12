package ai.giskard.repository.ml;

import ai.giskard.domain.DatasetProcessFunction;
import org.springframework.data.repository.NoRepositoryBean;

import java.util.List;

@NoRepositoryBean
public interface DatasetProcessFunctionRepository<E extends DatasetProcessFunction> extends CallableRepository<E> {

    List<E> findAllByProjectKeyNullOrProjectKey(String projectKey);

}
