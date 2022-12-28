package ai.giskard.repository;

import ai.giskard.domain.ml.Inspection;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

/**
 * Inspection repository
 */
public interface InspectionRepository extends JpaRepository<Inspection, Long> {
    List<Inspection> findAllByModelId(String modelId);

    List<Inspection> findAllByDatasetId(String datasetId);
}
