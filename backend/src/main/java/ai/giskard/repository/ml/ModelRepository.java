package ai.giskard.repository.ml;

import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.MappableJpaRepository;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ModelRepository extends MappableJpaRepository<ProjectModel, Long> {
    List<ProjectModel> findAllByProjectId(long projectId);

    default ProjectModel getById(long id) {
        return this.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT_MODEL, EntityNotFoundException.By.ID, id));
    }
}
