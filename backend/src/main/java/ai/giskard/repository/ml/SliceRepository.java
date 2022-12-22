package ai.giskard.repository.ml;

import ai.giskard.domain.Project;
import ai.giskard.domain.ml.Slice;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SliceRepository extends JpaRepository<Slice, Long> {
    List<Slice> findByProjectId(Long id);
}
