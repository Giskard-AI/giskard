package ai.giskard.repository.ml;

import ai.giskard.domain.ml.TestSuite;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface TestSuiteRepository extends JpaRepository<TestSuite, Long> {
    List<TestSuite> findAllByProjectId(long projectId);

    List<TestSuite> findAllByModelId(UUID modelId);

    @Query("FROM TestSuite where actualDataset.id = :id or referenceDataset.id = :id")
    List<TestSuite> findByDatasetId(@Param("id") UUID datasetId);

    List<TestSuite> findByModelId(UUID modelId);
}
