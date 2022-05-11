package ai.giskard.repository;

import ai.giskard.domain.Role;
import ai.giskard.domain.ml.Inspection;
import org.springframework.data.jpa.repository.JpaRepository;

/**
 * Spring Data JPA repository for the {@link Role} entity.
 */
public interface InspectionRepository extends JpaRepository<Inspection, String> {
}
