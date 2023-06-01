package ai.giskard.repository.ml;

import ai.giskard.domain.ml.TestSuite;
import ai.giskard.repository.MappableJpaRepository;
import ai.giskard.web.rest.errors.Entity;
import org.mapstruct.Named;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TestSuiteRepository extends MappableJpaRepository<TestSuite, Long> {
    @Override
    default Entity getEntityType() {
        return Entity.TEST_SUITE;
    }

    List<TestSuite> findAllByProjectId(Long projectId);

    TestSuite findOneByProjectIdAndId(Long projectId, Long id);


    @Named("no_mapstruct")
    @EntityGraph(attributePaths = {"functionInputs"})
    TestSuite getWithFunctionInputsById(Long id);

}
