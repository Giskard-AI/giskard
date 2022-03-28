package ai.giskard.repository.ml;

import ai.giskard.domain.ml.ProjectModel;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ModelRepository extends JpaRepository<ProjectModel, Long> {
    List<ProjectModel> findAllByProjectId(long projectId);
}
