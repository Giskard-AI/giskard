package ai.giskard.repository.ml;

import ai.giskard.domain.ml.testing.CodeBasedTestPreset;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CodeBasedTestPresetRepository extends JpaRepository<CodeBasedTestPreset, Long> {

}
