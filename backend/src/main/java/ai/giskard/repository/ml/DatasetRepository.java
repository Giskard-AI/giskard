package ai.giskard.repository.ml;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.repository.MappableJpaRepository;
import ai.giskard.web.rest.errors.Entity;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface DatasetRepository extends MappableJpaRepository<Dataset, UUID> {
    List<Dataset> findAllByProjectId(long projectId);

    @Override
    default Entity getEntityType() {
        return Entity.DATASET;
    }
}
