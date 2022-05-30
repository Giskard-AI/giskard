package ai.giskard.repository.ml;

import ai.giskard.domain.ml.TestSuite;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TestSuiteRepository extends JpaRepository<TestSuite, Long> {
    List<TestSuite> findAllByProjectId(long projectId);
}
