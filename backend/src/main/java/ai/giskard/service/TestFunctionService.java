package ai.giskard.service;

import ai.giskard.domain.TestFunction;
import ai.giskard.domain.TestFunctionArgument;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.web.dto.TestFunctionArgumentDTO;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import org.springframework.stereotype.Service;

import javax.transaction.Transactional;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service

public class TestFunctionService extends CallableService<TestFunction, TestFunctionDTO> {

    private final GiskardMapper giskardMapper;
    private final TestFunctionRepository testFunctionRepository;

    public TestFunctionService(TestFunctionRepository testFunctionRepository, GiskardMapper giskardMapper) {
        super(testFunctionRepository);
        this.giskardMapper = giskardMapper;
        this.testFunctionRepository = testFunctionRepository;
    }


    @Transactional
    public TestFunctionDTO save(TestFunctionDTO testFunction) {
        return giskardMapper.toDTO(testFunctionRepository.save(testFunctionRepository.findById(testFunction.getUuid())
            .map(existing -> update(existing, testFunction))
            .orElseGet(() -> create(testFunction))));
    }

    protected TestFunction create(TestFunctionDTO dto) {
        TestFunction function = giskardMapper.fromDTO(dto);
        if (function.getArgs() != null) {
            function.getArgs().forEach(arg -> arg.setTestFunction(function));
        }
        function.setVersion(testFunctionRepository.countByNameAndModule(function.getName(), function.getModule()) + 1);
        return function;
    }

    protected TestFunction update(TestFunction existing, TestFunctionDTO dto) {
        super.update(existing, dto);

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
                TestFunctionArgument createdArg = giskardMapper.fromDTO(currentArg);
                createdArg.setTestFunction(existing);
                existing.getArgs().add(createdArg);
            }
        });

        return existing;
    }

}
