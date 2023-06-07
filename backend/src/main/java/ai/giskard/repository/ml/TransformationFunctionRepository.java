package ai.giskard.repository.ml;

import ai.giskard.domain.TransformationFunction;
import ai.giskard.web.rest.errors.Entity;
import org.springframework.stereotype.Repository;

@Repository
public interface TransformationFunctionRepository extends CallableRepository<TransformationFunction> {

    @Override
    default Entity getEntityType() {
        return Entity.TRANSFORMATION_FUNCTION;
    }
}
