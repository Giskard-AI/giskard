package ai.giskard.repository;

import ai.giskard.domain.ml.TestSuiteExecution;
import org.springframework.data.jpa.repository.JpaRepository;

/**
 * TestSuiteExecution repository
 */
public interface TestSuiteExecutionRepository extends JpaRepository<TestSuiteExecution, Long> {

}
