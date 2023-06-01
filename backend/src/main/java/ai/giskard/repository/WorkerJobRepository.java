package ai.giskard.repository;

import ai.giskard.domain.WorkerJob;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.NoRepositoryBean;

import java.util.List;

@NoRepositoryBean
public interface WorkerJobRepository<S extends WorkerJob> extends JpaRepository<S, Long> {
    @Query("""
        SELECT e
        FROM #{#entityName} e
        WHERE e.completionDate IS NULL
        """)
    List<S> findRunningJobs();

}
