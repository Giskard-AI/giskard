package ai.giskard.repository.ml;

import ai.giskard.domain.DatasetProcessFunction;
import org.springframework.data.repository.NoRepositoryBean;

@NoRepositoryBean
public interface DatasetProcessFunctionRepository<E extends DatasetProcessFunction> extends CallableRepository<E> {

}
