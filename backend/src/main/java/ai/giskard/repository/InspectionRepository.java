package ai.giskard.repository;

import ai.giskard.domain.ml.Inspection;
import org.springframework.data.jpa.repository.JpaRepository;

/**
 * Inspection repository
 */
public interface InspectionRepository extends JpaRepository<Inspection, Long> {
}
