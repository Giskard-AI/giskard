package ai.giskard.service;

import ai.giskard.domain.Callable;
import ai.giskard.repository.ml.CallableRepository;
import ai.giskard.web.dto.CallableDTO;
import lombok.RequiredArgsConstructor;

import javax.transaction.Transactional;
import java.util.Collection;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

@RequiredArgsConstructor
public abstract class CallableService<E extends Callable, D extends CallableDTO> {

    private final CallableRepository<E> callableRepository;

    @Transactional
    public void saveAll(Collection<D> functions) {
        Map<UUID, E> existing = callableRepository.findAllById(functions.stream()
                .map(D::getUuid)
                .toList())
            .stream()
            .collect(Collectors.toMap(E::getUuid, Function.identity()));

        callableRepository.saveAll(functions.stream()
            .map(fn -> {
                if (existing.containsKey(fn.getUuid())) {
                    return update(existing.get(fn.getUuid()), fn);
                } else {
                    return create(fn);
                }
            })
            .toList());
    }

    protected abstract E create(D dto);

    protected E update(E existing, D dto) {
        existing.setDoc(dto.getDoc());
        existing.setModuleDoc(dto.getModuleDoc());
        existing.setCode(dto.getCode());
        existing.setTags(dto.getTags());

        return existing;
    }
}
