package ai.giskard.service;

import ai.giskard.domain.Callable;
import ai.giskard.domain.FunctionArgument;
import ai.giskard.repository.ml.CallableRepository;
import ai.giskard.utils.TransactionUtils;
import ai.giskard.web.dto.CallableDTO;
import ai.giskard.web.dto.TestFunctionArgumentDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

@RequiredArgsConstructor
public abstract class CallableService<E extends Callable, D extends CallableDTO> {

    protected final CallableRepository<E> callableRepository;
    protected final GiskardMapper giskardMapper;

    @Transactional(readOnly = true)
    public E getInitialized(UUID uuid) {
        E callable = callableRepository.getMandatoryById(uuid);
        TransactionUtils.initializeCallable(callable);
        return callable;
    }

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

        Map<String, FunctionArgument> existingArgs = existing.getArgs() != null ? existing.getArgs().stream()
            .collect(Collectors.toMap(FunctionArgument::getName, Function.identity())) : new HashMap<>();
        Map<String, TestFunctionArgumentDTO> currentArgs = dto.getArgs() != null ? dto.getArgs().stream()
            .collect(Collectors.toMap(TestFunctionArgumentDTO::getName, Function.identity())) : new HashMap<>();

        // Delete removed args
        existingArgs.entrySet().stream()
            .filter(entry -> !currentArgs.containsKey(entry.getKey()))
            .forEach(entry -> existing.getArgs().remove(entry.getValue()));

        // Update or create current args
        currentArgs.forEach((name, currentArg) -> {
            if (existingArgs.containsKey(name)) {
                FunctionArgument existingArg = existingArgs.get(name);
                existingArg.setType(currentArg.getType());
                existingArg.setOptional(currentArg.isOptional());
                existingArg.setDefaultValue(currentArg.getDefaultValue());
            } else {
                FunctionArgument createdArg = giskardMapper.fromDTO(currentArg);
                createdArg.setFunction(existing);
                existing.getArgs().add(createdArg);
            }
        });

        return existing;
    }
}
