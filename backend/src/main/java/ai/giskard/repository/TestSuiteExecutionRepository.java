package ai.giskard.repository;

import ai.giskard.domain.ml.TestSuiteExecution;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

/**
 * TestSuiteExecution repository
 */
public interface TestSuiteExecutionRepository extends JpaRepository<TestSuiteExecution, Long> {

    List<TestSuiteExecution> findAllBySuiteIdOrderByExecutionDateDesc(long suiteId);

}
