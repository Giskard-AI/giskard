package ai.giskard.repository.ml;

import ai.giskard.domain.TestFunction;
import ai.giskard.domain.ml.testing.Test;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface TestFunctionRepository extends JpaRepository<TestFunction, UUID> {

    int countByNameAndModule(String name, String module);
}
