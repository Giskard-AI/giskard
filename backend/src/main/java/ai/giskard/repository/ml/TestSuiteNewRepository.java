package ai.giskard.repository.ml;

import ai.giskard.domain.ml.TestSuiteNew;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TestSuiteNewRepository extends JpaRepository<TestSuiteNew, Long> {
    List<TestSuiteNew> findAllByProjectKey(String projectKey);
    List<TestSuiteNew> findAllByProjectId(Long projectId);

    TestSuiteNew findOneByProjectIdAndId(Long projectId, Long id);


}
