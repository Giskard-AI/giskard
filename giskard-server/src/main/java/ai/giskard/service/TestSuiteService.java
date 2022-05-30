package ai.giskard.service;

import ai.giskard.domain.ml.CodeTestTemplate;
import ai.giskard.domain.ml.ModelType;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.repository.ml.TestRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.TestSuiteDTO;
import ai.giskard.web.dto.ml.UpdateTestSuiteDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

@Service
@Transactional
@RequiredArgsConstructor
public class TestSuiteService {
    private final Logger log = LoggerFactory.getLogger(TestSuiteService.class);

    private final TestSuiteRepository testSuiteRepository;
    private final TestRepository testRepository;
    private final GiskardMapper giskardMapper;
    private final CodeTestTemplateService testTemplateService;


    public TestSuite updateTestSuite(UpdateTestSuiteDTO dto) {
        TestSuite testSuite = testSuiteRepository.findById(dto.getId()).orElseThrow(() -> new EntityNotFoundException(Entity.TEST_SUITE, dto.getId()));
        giskardMapper.updateTestSuiteFromDTO(dto, testSuite);
        return testSuite;
    }

    public void deleteSuite(Long suiteId) {
        testRepository.deleteAllByTestSuiteId(suiteId);
        testSuiteRepository.deleteById(suiteId);
    }

    public TestSuiteDTO createTestSuite(TestSuite testSuite, boolean shouldGenerateTests) {
        TestSuite ts = testSuiteRepository.save(testSuite);
        if (shouldGenerateTests) {
            generateTests(ts);
        }
        return giskardMapper.testSuiteToTestSuiteDTO(ts);
    }

    private void generateTests(TestSuite suite) {
        ModelType modelType = suite.getModel().getModelType();
        List<Test> generatedTests = new ArrayList<>();
        for (CodeTestTemplate template : testTemplateService.getAllTemplates()) {
            Set<ModelType> templateModelTypes = template.getModelTypes();
            if (templateModelTypes == null || templateModelTypes.contains(modelType)) {
                Test test = Test.builder()
                    .testSuite(suite)
                    .name(template.getTitle())
                    .code(template.getCode())
                    .build();
                generatedTests.add(test);
                suite.getTests().add(test);
            }
        }
        log.info("Generated {} tests for test suite {}", generatedTests.size(), suite.getId());
        testRepository.saveAll(generatedTests);
    }
}
