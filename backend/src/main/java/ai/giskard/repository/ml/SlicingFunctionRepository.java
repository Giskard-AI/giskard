package ai.giskard.repository.ml;

import ai.giskard.domain.SlicingFunction;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface SlicingFunctionRepository extends CallableRepository<SlicingFunction> {

    default SlicingFunction getById(UUID id) {
        return this.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.SLICING_FUNCTION, EntityNotFoundException.By.ID, id));
    }

}
