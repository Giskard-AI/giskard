package ai.giskard.repository.ml;

import ai.giskard.domain.ml.TestSuiteNew;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TestSuiteNewRepository extends JpaRepository<TestSuiteNew, Long> {

    default TestSuiteNew getById(long id) {
        return this.findById(id)
            .orElseThrow(() -> new EntityNotFoundException(Entity.TEST_SUITE, EntityNotFoundException.By.ID, id));
    }

    List<TestSuiteNew> findAllByProjectId(Long projectId);

    TestSuiteNew findOneByProjectIdAndId(Long projectId, Long id);


}
