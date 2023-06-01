package ai.giskard.service;

import ai.giskard.domain.TestFunction;
import ai.giskard.domain.TestFunctionArgument;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.service.ml.MLWorkerCacheService;
import ai.giskard.web.dto.TestFunctionArgumentDTO;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import javax.transaction.Transactional;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;

@Service
@RequiredArgsConstructor
public class TestFunctionService {

    private final GiskardMapper giskardMapper;
    private final TestFunctionRepository testFunctionRepository;
    private final ProjectRepository projectRepository;
    private final MLWorkerCacheService mlWorkerCacheService;

    @Transactional
    public void saveAll(Collection<TestFunctionDTO> testFunctions) {
        Map<UUID, TestFunction> existing = testFunctionRepository.findAllById(testFunctions.stream()
                .map(TestFunctionDTO::getUuid)
                .toList())
            .stream()
            .collect(Collectors.toMap(TestFunction::getUuid, Function.identity()));

        testFunctionRepository.saveAll(testFunctions.stream()
            .map(testFunction -> {
                if (existing.containsKey(testFunction.getUuid())) {
                    return update(existing.get(testFunction.getUuid()), testFunction);
                } else {
                    return create(testFunction);
                }
            })
            .toList());
    }

    @Transactional
    public TestFunctionDTO save(TestFunctionDTO testFunction) {
        return giskardMapper.toDTO(testFunctionRepository.save(testFunctionRepository.findById(testFunction.getUuid())
            .map(existing -> update(existing, testFunction))
            .orElseGet(() -> create(testFunction))));
    }

    private TestFunction create(TestFunctionDTO dto) {
        TestFunction function = giskardMapper.fromDTO(dto);
        if (function.getArgs() != null) {
            function.getArgs().forEach(arg -> arg.setTestFunction(function));
        }
        function.setVersion(testFunctionRepository.countByNameAndModule(function.getName(), function.getModule()) + 1);
        return function;
    }

    private TestFunction update(TestFunction existing, TestFunctionDTO dto) {
        existing.setDoc(dto.getDoc());
        existing.setModuleDoc(dto.getModuleDoc());
        existing.setCode(dto.getCode());
        existing.setTags(dto.getTags());

        Map<String, TestFunctionArgument> existingArgs = existing.getArgs() != null ? existing.getArgs().stream()
            .collect(Collectors.toMap(TestFunctionArgument::getName, Function.identity())) : new HashMap<>();
        Map<String, TestFunctionArgumentDTO> currentArgs = dto.getArgs() != null ? dto.getArgs().stream()
            .collect(Collectors.toMap(TestFunctionArgumentDTO::getName, Function.identity())) : new HashMap<>();

        // Delete removed args
        existingArgs.entrySet().stream()
            .filter(entry -> !currentArgs.containsKey(entry.getKey()))
            .forEach(entry -> existing.getArgs().remove(entry.getValue()));

        // Update or create current args
        currentArgs.forEach((name, currentArg) -> {
            if (existingArgs.containsKey(name)) {
                TestFunctionArgument existingArg = existingArgs.get(name);
                existingArg.setType(currentArg.getType());
                existingArg.setOptional(currentArg.isOptional());
                existingArg.setDefaultValue(currentArg.getDefaultValue());
            } else {
                existing.getArgs().add(giskardMapper.fromDTO(currentArg));
            }
        });

        return existing;
    }

    @Transactional
    public List<TestFunctionDTO> findAll(long projectId) {
        return Stream.concat(testFunctionRepository.findAll().stream().map(giskardMapper::toDTO),
                mlWorkerCacheService.findGiskardTest(projectRepository.getById(projectId).isUsingInternalWorker()).stream())
            .toList();
    }

}
