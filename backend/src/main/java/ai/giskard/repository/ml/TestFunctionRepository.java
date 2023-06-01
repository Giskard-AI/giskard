package ai.giskard.repository.ml;

import ai.giskard.domain.TestFunction;
import ai.giskard.web.rest.errors.Entity;
import org.mapstruct.Named;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface TestFunctionRepository extends CallableRepository<TestFunction> {
    @Override
    default Entity getEntityType() {
        return Entity.TEST_FUNCTION;
    }

    @EntityGraph(attributePaths = {"args"})
    @Named("no_mapstruct")
    TestFunction getWithArgsByUuid(UUID id);
}
