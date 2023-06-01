package ai.giskard.repository.ml;

import ai.giskard.domain.ml.TestSuiteNew;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface TestSuiteNewRepository extends JpaRepository<TestSuiteNew, Long> {
}
