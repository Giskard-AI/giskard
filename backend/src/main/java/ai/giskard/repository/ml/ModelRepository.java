package ai.giskard.repository.ml;

import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.mapstruct.Named;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ModelRepository extends JpaRepository<ProjectModel, String> {
    List<ProjectModel> findAllByProjectId(long projectId);

    default ProjectModel getById(String id) {
        return this.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT_MODEL, EntityNotFoundException.By.ID, id));
    }

    @Override
    @Named("_noop_")
    ProjectModel getOne(String s);
}
