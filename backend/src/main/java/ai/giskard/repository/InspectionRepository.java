package ai.giskard.repository;

import ai.giskard.domain.ml.Inspection;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

/**
 * Inspection repository
 */
public interface InspectionRepository extends JpaRepository<Inspection, Long> {
    List<Inspection> findAllByModelId(UUID modelId);

    List<Inspection> findAllByDatasetId(UUID datasetId);

    List<Inspection> findAllByModelProjectId(long projectId);

    default Inspection getById(long id) {
        return this.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.INSPECTION, EntityNotFoundException.By.ID, id));
    }
}
