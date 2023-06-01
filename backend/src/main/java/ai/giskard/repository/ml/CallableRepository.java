package ai.giskard.repository.ml;

import ai.giskard.domain.Callable;
import ai.giskard.repository.MappableJpaRepository;
import org.springframework.data.repository.NoRepositoryBean;

import java.util.List;
import java.util.UUID;

@NoRepositoryBean
public interface CallableRepository<E extends Callable> extends MappableJpaRepository<E, UUID> {

    int countByNameAndModule(String name, String module);

    List<E> findAllByTags(String tag);

    default List<E> findAllPickles() {
        return findAllByTags("pickle");
    }


}
