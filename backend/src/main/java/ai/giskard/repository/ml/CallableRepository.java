package ai.giskard.repository.ml;

import ai.giskard.domain.Callable;
import ai.giskard.repository.MappableJpaRepository;
import org.springframework.data.repository.NoRepositoryBean;

import java.util.Collection;
import java.util.List;
import java.util.UUID;
import java.util.function.Predicate;
import java.util.stream.Collectors;

@NoRepositoryBean
public interface CallableRepository<E extends Callable> extends MappableJpaRepository<E, UUID> {

    int countByDisplayName(String displayName);

    default List<E> saveAllIfNotExists(Collection<E> entities) {
        List<E> existing = findAllById(entities.stream().map(E::getUuid).collect(Collectors.toSet()));

        entities.stream()
            .filter(Predicate.not(existing::contains))
            .forEach(callable -> callable.getArgs().forEach(functionArgument -> functionArgument.setFunction(callable)));
        return saveAll(entities.stream()
            .filter(Predicate.not(existing::contains))
            .toList()
        );
    }

}
