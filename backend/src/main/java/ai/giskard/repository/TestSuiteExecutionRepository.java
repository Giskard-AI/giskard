package ai.giskard.repository;

import ai.giskard.domain.ml.TestSuiteExecution;

import java.util.List;

/**
 * TestSuiteExecution repository
 */
public interface TestSuiteExecutionRepository extends WorkerJobRepository<TestSuiteExecution> {

    List<TestSuiteExecution> findAllBySuiteIdOrderByExecutionDateDesc(long suiteId);

}
