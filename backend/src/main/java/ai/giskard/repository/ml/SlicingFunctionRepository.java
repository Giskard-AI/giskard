package ai.giskard.repository.ml;

import ai.giskard.domain.SlicingFunction;
import ai.giskard.web.rest.errors.Entity;
import org.springframework.stereotype.Repository;

@Repository
public interface SlicingFunctionRepository extends DatasetProcessFunctionRepository<SlicingFunction> {
    @Override
    default Entity getEntityType() {
        return Entity.SLICING_FUNCTION;
    }
}
