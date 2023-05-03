package ai.giskard.repository;

import ai.giskard.domain.ml.Inspection;
import ai.giskard.web.rest.errors.Entity;

import java.util.List;
import java.util.UUID;

/**
 * Inspection repository
 */
public interface InspectionRepository extends MappableJpaRepository<Inspection, Long> {
    @Override
    default Entity getEntityType() {
        return Entity.INSPECTION;
    }

    List<Inspection> findAllByModelId(UUID modelId);

    List<Inspection> findAllByDatasetId(UUID datasetId);

    List<Inspection> findAllByModelProjectId(long projectId);
}
