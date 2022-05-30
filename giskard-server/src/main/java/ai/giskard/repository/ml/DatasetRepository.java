package ai.giskard.repository.ml;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.repository.MappableJpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DatasetRepository extends MappableJpaRepository<Dataset, Long> {
    List<Dataset> findAllByProjectId(long projectId);
}
