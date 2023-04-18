package ai.giskard.repository.ml;

import ai.giskard.domain.TransformationFunction;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface TransformationFunctionRepository extends CallableRepository<TransformationFunction> {

    default TransformationFunction getById(UUID id) {
        return this.findById(id)
            .orElseThrow(() -> new EntityNotFoundException(Entity.TRANSFORMATION_FUNCTION, EntityNotFoundException.By.ID, id));
    }

}
