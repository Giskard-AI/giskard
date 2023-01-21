package ai.giskard.service;

import ai.giskard.domain.ColumnMeaning;
import ai.giskard.domain.ml.*;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.repository.ml.TestRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.TestSuiteDTO;
import ai.giskard.web.dto.ml.UpdateTestSuiteDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.apache.commons.text.StringSubstitutor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Transactional
@RequiredArgsConstructor
public class TestSuiteService {
    private final Logger log = LoggerFactory.getLogger(TestSuiteService.class);

    private final TestSuiteRepository testSuiteRepository;
    private final TestRepository testRepository;
    private final DatasetRepository datasetRepository;
    private final ModelRepository modelRepository;
    private final GiskardMapper giskardMapper;
    private final CodeTestTemplateService testTemplateService;


    public TestSuite updateTestSuite(UpdateTestSuiteDTO dto) {
        TestSuite suite = testSuiteRepository.getById(dto.getId());
        if (dto.getActualDatasetId() != null && !suite.getProject().equals(datasetRepository.getById(dto.getActualDatasetId()).getProject())) {
            throw new IllegalArgumentException("Actual dataset is not part of the test project");
        }
        if (dto.getReferenceDatasetId() != null && !suite.getProject().equals(datasetRepository.getById(dto.getReferenceDatasetId()).getProject())) {
            throw new IllegalArgumentException("Reference dataset is not part of the test project");
        }
        if (dto.getModelId() != null && !suite.getProject().equals(modelRepository.getById(dto.getModelId()).getProject())) {
            throw new IllegalArgumentException("Model is not part of the test project");
        }

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
        List<Test> generatedTests = new ArrayList<>();
        for (CodeTestTemplate template : testTemplateService.getAllTemplates()) {
            if (!testTemplateService.doesTestTemplateSuiteTestSuite(suite, template)) {
                continue;
            }
            Test test = Test.builder()
                .testSuite(suite)
                .name(template.title)
                .code(replacePlaceholders(template.code, suite))
                .build();
            generatedTests.add(test);
            suite.getTests().add(test);
        }
        log.info("Generated {} tests for test suite {}", generatedTests.size(), suite.getId());
        testRepository.saveAll(generatedTests);
    }

    private String replacePlaceholders(String code, TestSuite suite) {
        Map<String, String> substitutions = new HashMap<>();

        ProjectModel model = suite.getModel();

        if (model.getModelType() == ModelType.CLASSIFICATION) {
            model.getClassificationLabels().stream().findFirst().ifPresent(label -> {
                substitutions.putIfAbsent("CLASSIFICATION LABEL", label);
            });
        }
        Dataset ds = suite.getReferenceDataset() != null ? suite.getReferenceDataset() : suite.getActualDataset();
        if (ds != null) {
            ds.getColumnMeanings().forEach((fName, fType) -> {
                if (fName.equals(ds.getTarget())) {
                    substitutions.putIfAbsent("TARGET NAME", fName);
                } else {
                    substitutions.putIfAbsent("FEATURE NAME", fName);
                    if (fType == ColumnMeaning.CATEGORY) {
                        substitutions.putIfAbsent("CATEGORICAL FEATURE NAME", fName);
                    }
                    if (fType == ColumnMeaning.NUMERIC) {
                        substitutions.putIfAbsent("NUMERIC FEATURE NAME", fName);
                    }
                    if (fType == ColumnMeaning.TEXT) {
                        substitutions.putIfAbsent("TEXTUAL FEATURE NAME", fName);
                    }
                }
            });
        }

        StringSubstitutor sub = new StringSubstitutor(substitutions, "{{", "}}");
        return sub.replace(code);
    }
}
