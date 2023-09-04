package ai.giskard.service;

import ai.giskard.domain.TestFunction;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import org.apache.logging.log4j.util.Strings;
import org.springframework.stereotype.Service;

@Service

public class TestFunctionService extends CallableService<TestFunction, TestFunctionDTO> {

    private final TestFunctionRepository testFunctionRepository;

    public TestFunctionService(TestFunctionRepository testFunctionRepository, GiskardMapper giskardMapper) {
        super(testFunctionRepository, giskardMapper);
        this.testFunctionRepository = testFunctionRepository;
    }


    public TestFunctionDTO save(TestFunctionDTO testFunction) {
        return giskardMapper.toDTO(testFunctionRepository.save(testFunctionRepository.findById(testFunction.getUuid())
            .map(existing -> update(existing, testFunction))
            .orElseGet(() -> create(testFunction))));
    }

    protected TestFunction create(TestFunctionDTO dto) {
        TestFunction function = giskardMapper.fromDTO(dto);
        if (function.getArgs() != null) {
            function.getArgs().forEach(arg -> arg.setFunction(function));
        }

        if (Strings.isBlank(function.getDisplayName())) {
            function.setDisplayName(function.getModule() + "." + function.getName());
        }

        function.setVersion(testFunctionRepository.countByDisplayName(function.getDisplayName()) + 1);

        return function;
    }

}
