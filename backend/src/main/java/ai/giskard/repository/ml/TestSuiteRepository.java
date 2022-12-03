package ai.giskard.repository.ml;

import ai.giskard.domain.ml.TestSuite;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TestSuiteRepository extends JpaRepository<TestSuite, Long> {
    List<TestSuite> findAllByProjectId(long projectId);

    List<TestSuite> findAllByModelId(long modelId);

    @Modifying
    @Query("FROM TestSuite where actualDataset.id = :id or referenceDataset.id = :id")
    List<TestSuite> findByDatasetId(@Param("id") long datasetId);

    List<TestSuite> findByModelId(long modelId);
}
