package ai.giskard.service;

import ai.giskard.domain.FeatureType;
import ai.giskard.domain.ml.*;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.jobs.JobType;
import ai.giskard.repository.ml.*;
import ai.giskard.web.dto.TestFunctionArgumentDTO;
import ai.giskard.web.dto.TestSuiteNewDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.TestSuiteDTO;
import ai.giskard.web.dto.ml.UpdateTestSuiteDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Maps;
import lombok.RequiredArgsConstructor;
import org.apache.commons.text.StringSubstitutor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

import static ai.giskard.web.rest.errors.Entity.TEST;
import static ai.giskard.web.rest.errors.Entity.TEST_SUITE;

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
    private final TestSuiteNewRepository testSuiteNewRepository;
    private final TestService testService;
    private final TestSuiteExecutionService testSuiteExecutionService;
    private final JobService jobService;

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
            model.getClassificationLabels().stream().findFirst().ifPresent(label -> substitutions.putIfAbsent("CLASSIFICATION LABEL", label));
        }
        Dataset ds = suite.getReferenceDataset() != null ? suite.getReferenceDataset() : suite.getActualDataset();
        if (ds != null) {
            ds.getFeatureTypes().forEach((fName, fType) -> {
                if (fName.equals(ds.getTarget())) {
                    substitutions.putIfAbsent("TARGET NAME", fName);
                } else {
                    substitutions.putIfAbsent("FEATURE NAME", fName);
                    if (fType == FeatureType.CATEGORY) {
                        substitutions.putIfAbsent("CATEGORICAL FEATURE NAME", fName);
                    }
                    if (fType == FeatureType.NUMERIC) {
                        substitutions.putIfAbsent("NUMERIC FEATURE NAME", fName);
                    }
                    if (fType == FeatureType.TEXT) {
                        substitutions.putIfAbsent("TEXTUAL FEATURE NAME", fName);
                    }
                }
            });
        }

        StringSubstitutor sub = new StringSubstitutor(substitutions, "{{", "}}");
        return sub.replace(code);
    }

    public Map<String, String> getSuiteInputs(Long projectId, Long suiteId) {
        TestSuiteNew suite = testSuiteNewRepository.findOneByProjectIdAndId(projectId, suiteId);

        Map<String, String> res = new HashMap<>();

        suite.getTests().forEach(test -> {
            Collection<TestFunctionArgument> signatureArgs = test.getTestFunction().getArgs();
            ImmutableMap<String, TestInput> providedInputs = Maps.uniqueIndex(test.getTestInputs(), TestInput::getName);

            signatureArgs.stream()
                .filter(a -> !a.isOptional())
                .forEach(a -> {
                    String name = null;
                    if (!providedInputs.containsKey(a.getName())) {
                        name = a.getName();
                    } else if (providedInputs.get(a.getName()).isAlias()) {
                        name = providedInputs.get(a.getName()).getValue();
                    }
                    if (name != null) {
                        if (res.containsKey(name) && !a.getType().equals(res.get(name))) {
                            throw new IllegalArgumentException("Variable with name %s is declared as %s and %s at the same time".formatted(a.getName(), res.get(a.getName()), a.getType()));
                        }
                        res.put(name, a.getType());
                    }
                });
        });
        return res;
    }


    @Transactional
    public UUID scheduleTestSuiteExecution(Long projectId, Long suiteId, Map<String, String> inputs) {
        TestSuiteNew testSuite = testSuiteNewRepository.findById(suiteId)
            .orElseThrow(() -> new EntityNotFoundException(TEST_SUITE, suiteId));

        TestSuiteExecution execution = new TestSuiteExecution(testSuite);
        execution.setInputs(inputs.entrySet().stream()
            .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue)));

        Map<String, String> suiteInputs = getSuiteInputs(projectId, suiteId);

        verifyAllInputProvided(inputs, testSuite, suiteInputs);

        return jobService.undetermined(() ->
            testSuiteExecutionService.executeScheduledTestSuite(execution, suiteInputs), projectId, JobType.TEST_SUITE_EXECUTION,
            testSuite.getProject().getMlWorkerType());
    }

    private static void verifyAllInputProvided(Map<String, String> providedInputs,
                                               TestSuiteNew testSuite,
                                               Map<String, String> requiredInputs) {
        List<String> missingInputs = requiredInputs.keySet().stream()
            .filter(requiredInput -> !providedInputs.containsKey(requiredInput))
            .toList();
        if (!missingInputs.isEmpty()) {
            throw new IllegalArgumentException("Inputs '%s' required to execute test suite %s"
                .formatted(String.join(", ", missingInputs), testSuite.getName()));
        }
    }

    public TestSuiteNewDTO updateTestInputs(long suiteId, String testId, Map<String, String> inputs) {
        TestSuiteNew testSuite = testSuiteNewRepository.findById(suiteId)
            .orElseThrow(() -> new EntityNotFoundException(TEST_SUITE, suiteId));

        SuiteTest test = testSuite.getTests().stream()
            .filter(t -> testId.equals(t.getTestId()))
            .findFirst().orElseThrow(() -> new EntityNotFoundException(TEST, testId));

        verifyAllInputExists(inputs, test);

        test.getTestInputs().clear();
        test.getTestInputs().addAll(inputs.entrySet().stream()
                .filter(entry -> entry.getValue() != null)
            .map(entry -> new TestInput(entry.getKey(), entry.getValue(), test))
            .toList());

        return giskardMapper.toDTO(testSuiteNewRepository.save(testSuite));
    }

    private void verifyAllInputExists(Map<String, String> providedInputs,
                                      SuiteTest test ) {
        TestCatalogDTO catalog = testService.listTestsFromRegistry(test.getSuite().getProject().getId());
        TestDefinitionDTO testDefinition = catalog.getTests().get(test.getTestId());

        Map<String, String> requiredInputs = testDefinition.getArguments().entrySet().stream()
            .collect(Collectors.toMap(Map.Entry::getKey, entry -> entry.getValue().getType()));

        List<String> nonExistingInputs = providedInputs.keySet().stream()
            .filter(providedInput -> !requiredInputs.containsKey(providedInput))
            .toList();

        if (!nonExistingInputs.isEmpty()) {
            throw new IllegalArgumentException("Inputs '%s' does not exists for test %s"
                .formatted(String.join(", ", nonExistingInputs), testDefinition.getName()));
        }
    }
}
