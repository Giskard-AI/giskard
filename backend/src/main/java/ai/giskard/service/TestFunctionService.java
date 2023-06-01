package ai.giskard.service;

import ai.giskard.domain.TestFunction;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import javax.transaction.Transactional;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TestFunctionService {

    private final GiskardMapper giskardMapper;
    private final TestFunctionRepository testFunctionRepository;

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
        function.setVersion(testFunctionRepository.countByNameAndModule(function.getName(), function.getModule()) + 1);
        return function;
    }

    private TestFunction update(TestFunction existing, TestFunctionDTO dto) {
        existing.setDoc(dto.getDoc());
        existing.setModuleDoc(dto.getModuleDoc());
        existing.setCode(dto.getCode());
        existing.setTags(dto.getTags());

        return existing;
    }

}
