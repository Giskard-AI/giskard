package ai.giskard.repository.ml;

import ai.giskard.domain.Callable;
import ai.giskard.repository.MappableJpaRepository;
import org.springframework.data.repository.NoRepositoryBean;

import java.util.UUID;

@NoRepositoryBean
public interface CallableRepository<E extends Callable> extends MappableJpaRepository<E, UUID> {

    int countByDisplayName(String displayName);

}
