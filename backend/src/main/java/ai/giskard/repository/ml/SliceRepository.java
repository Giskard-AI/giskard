package ai.giskard.repository.ml;

import ai.giskard.domain.ml.Slice;
import ai.giskard.repository.MappableJpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SliceRepository extends MappableJpaRepository<Slice, Long> {
    List<Slice> findByProjectId(Long id);
}
