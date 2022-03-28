package ai.giskard.repository.ml;

import ai.giskard.domain.ml.Dataset;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DatasetRepository extends JpaRepository<Dataset, Long> {
    List<Dataset> findAllByProjectId(long projectId);
}
