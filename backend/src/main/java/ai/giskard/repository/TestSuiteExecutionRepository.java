package ai.giskard.repository;

import ai.giskard.domain.ml.TestSuiteExecution;

import java.util.List;

/**
 * TestSuiteExecution repository
 */
public interface TestSuiteExecutionRepository extends MappableJpaRepository<TestSuiteExecution, Long> {

    List<TestSuiteExecution> findAllBySuiteIdOrderByExecutionDateDesc(long suiteId);

}
