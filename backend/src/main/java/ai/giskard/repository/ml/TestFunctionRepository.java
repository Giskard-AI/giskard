package ai.giskard.repository.ml;

import ai.giskard.domain.TestFunction;
import ai.giskard.repository.MappableJpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface TestFunctionRepository extends MappableJpaRepository<TestFunction, UUID> {

    int countByNameAndModule(String name, String module);
}
