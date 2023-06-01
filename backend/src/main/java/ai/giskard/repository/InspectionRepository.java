package ai.giskard.repository;

import ai.giskard.domain.ml.Inspection;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

/**
 * Inspection repository
 */
public interface InspectionRepository extends JpaRepository<Inspection, Long> {
    List<Inspection> findAllByModelId(UUID modelId);

    List<Inspection> findAllByDatasetId(UUID datasetId);
}
