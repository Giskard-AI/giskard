package ai.giskard.repository.ml;

import ai.giskard.domain.ml.TestSuite;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TestSuiteRepository extends JpaRepository<TestSuite, Long> {

    default TestSuite getById(long id) {
        return this.findById(id)
            .orElseThrow(() -> new EntityNotFoundException(Entity.TEST_SUITE, EntityNotFoundException.By.ID, id));
    }

    List<TestSuite> findAllByProjectId(Long projectId);

    TestSuite findOneByProjectIdAndId(Long projectId, Long id);


}
