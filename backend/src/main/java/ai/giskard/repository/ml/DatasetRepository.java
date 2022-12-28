package ai.giskard.repository.ml;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.mapstruct.Named;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

import static ai.giskard.web.rest.errors.EntityNotFoundException.By;

@Repository
public interface DatasetRepository extends JpaRepository<Dataset, String> {
    List<Dataset> findAllByProjectId(long projectId);

    @Override
    @Named("_noop_")
    Dataset getOne(String s);

    default Dataset getById(String id) {
        return this.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.DATASET, By.ID, id));
    }
}
