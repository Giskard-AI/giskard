package ai.giskard.repository.ml;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.repository.MappableJpaRepository;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.springframework.stereotype.Repository;

import java.util.List;

import static ai.giskard.web.rest.errors.EntityNotFoundException.*;

@Repository
public interface DatasetRepository extends MappableJpaRepository<Dataset, Long> {
    List<Dataset> findAllByProjectId(long projectId);

    default Dataset getById(long id) {
        return this.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.DATASET, By.ID, id));
    }
}
