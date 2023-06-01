package ai.giskard.repository.ml;

import ai.giskard.domain.ml.TestInput;
import ai.giskard.repository.MappableJpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface TestInputRepository extends MappableJpaRepository<TestInput, Long> {

}
