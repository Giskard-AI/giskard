package ai.giskard.repository.ml;

import ai.giskard.domain.ml.testing.Test;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TestRepository extends JpaRepository<Test, Long> {
    List<Test> findAllByTestSuiteId(long testSuiteId);
}
