package ai.giskard.repository.ml;

import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.MappableJpaRepository;
import ai.giskard.web.rest.errors.Entity;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ModelRepository extends MappableJpaRepository<ProjectModel, UUID> {
    List<ProjectModel> findAllByProjectId(long projectId);

    @Override
    default Entity getEntityType() {
        return Entity.PROJECT_MODEL;
    }
}
