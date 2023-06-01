package ai.giskard.service;

import ai.giskard.domain.TestFunction;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import javax.transaction.Transactional;

@Service
@RequiredArgsConstructor
public class TestFunctionService {

    private final GiskardMapper giskardMapper;
    private final TestFunctionRepository testFunctionRepository;

    @Transactional
    public TestFunctionDTO save(TestFunctionDTO testFunction) {
        return testFunctionRepository.findById(testFunction.getUuid())
            .map(existing -> update(existing, testFunction))
            .orElseGet(() -> create(testFunction));
    }

    private TestFunctionDTO create(TestFunctionDTO dto) {
        TestFunction function = giskardMapper.fromDTO(dto);
        function.setVersion(testFunctionRepository.countByNameAndModule(function.getName(), function.getModule()) + 1);
        return giskardMapper.toDTO(testFunctionRepository.save(function));
    }

    private TestFunctionDTO update(TestFunction existing, TestFunctionDTO dto) {
        existing.setDoc(dto.getDoc());
        existing.setModuleDoc(dto.getModuleDoc());
        existing.setCode(dto.getCode());
        existing.setTags(dto.getTags());

        return giskardMapper.toDTO(testFunctionRepository.save(existing));
    }

}
