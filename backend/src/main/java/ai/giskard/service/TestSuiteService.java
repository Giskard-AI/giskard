package ai.giskard.service;

import ai.giskard.domain.ColumnMeaning;
import ai.giskard.domain.ml.*;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.TestSuiteExecutionRepository;
import ai.giskard.repository.ml.*;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.TestCatalogDTO;
import ai.giskard.web.dto.TestFunctionArgumentDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.TestSuiteDTO;
import ai.giskard.web.dto.ml.TestSuiteExecutionDTO;
import ai.giskard.web.dto.ml.UpdateTestSuiteDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.worker.RunTestSuiteRequest;
import ai.giskard.worker.TestFunction;
import ai.giskard.worker.TestRegistryResponse;
import ai.giskard.worker.TestSuiteResultMessage;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Maps;
import com.google.protobuf.Empty;
import lombok.RequiredArgsConstructor;
import org.apache.commons.text.StringSubstitutor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;

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
    private final MLWorkerService mlWorkerService;
    private final ProjectRepository projectRepository;
    private final TestArgumentService testArgumentService;
    private final TestSuiteExecutionRepository testSuiteExecutionRepository;

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

    public Map<String, String> getSuiteInputs(Long projectId, Long suiteId) {
        TestSuiteNew suite = testSuiteNewRepository.findOneByProjectIdAndId(projectId, suiteId);
        TestCatalogDTO catalog = testService.listTestsFromRegistry(projectId);

        Map<String, String> res = new HashMap<>();

        suite.getTests().forEach(test -> {
            Collection<TestFunctionArgumentDTO> signatureArgs = catalog.getTests().get(test.getTestId()).getArguments().values();
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


    public TestSuiteExecutionDTO executeTestSuite(Long projectId, Long suiteId, Map<String, Object> inputs) {
        try (MLWorkerClient client = mlWorkerService.createClient(projectRepository.getById(projectId).isUsingInternalWorker())) {
            TestRegistryResponse response = client.getBlockingStub().getTestRegistry(Empty.newBuilder().build());
            Map<String, TestFunction> registry = response.getTestsMap().values().stream()
                .collect(Collectors.toMap(TestFunction::getId, Function.identity()));

            TestSuiteNew testSuite = testSuiteNewRepository.findById(suiteId)
                .orElseThrow(() -> new EntityNotFoundException(TEST_SUITE, suiteId));

            RunTestSuiteRequest.Builder builder = RunTestSuiteRequest.newBuilder()
                .addAllTestId(testSuite.getTests().stream()
                    .map(test -> String.valueOf(test.getTestId()))
                    .toList());

            Map<String, String> suiteInputs = getSuiteInputs(projectId, suiteId);

            verifyAllInputProvided(inputs, testSuite, suiteInputs);

            for (Map.Entry<String, Object> entry : inputs.entrySet()) {
                builder.addGlobalArguments(testArgumentService.buildTestArgument(suiteInputs, entry.getKey(), entry.getValue()));
            }

            for (SuiteTest suiteTest : testSuite.getTests()) {
                builder.addFixedArguments(testArgumentService.buildFixedTestArgument(suiteTest, registry.get(suiteTest.getTestId())));
            }

            TestSuiteExecution execution = new TestSuiteExecution(testSuite);
            execution.setInputs(inputs.entrySet().stream()
                .collect(Collectors.toMap(Map.Entry::getKey, entry -> String.valueOf(entry.getValue()))));
            try {
                TestSuiteResultMessage testSuiteResultMessage = client.getBlockingStub().runTestSuite(builder.build());

                Map<String, SuiteTest> tests = testSuite.getTests().stream()
                    .collect(Collectors.toMap(SuiteTest::getTestId, Function.identity()));

                execution.setResult(testSuiteResultMessage.getIsPass() ? TestResult.PASSED : TestResult.FAILED);
                execution.setResults(testSuiteResultMessage.getResultsList().stream()
                    .map(namedSingleTestResult ->
                        new SuiteTestExecution(tests.get(namedSingleTestResult.getName()), execution, namedSingleTestResult.getResult()))
                    .toList());
            } catch (Exception e) {
                log.error("Error while executing test suite {}", testSuite.getName(), e);
                execution.setResult(TestResult.ERROR);
            }

            return giskardMapper.toDto(testSuiteExecutionRepository.save(execution));

        }
    }

    private static void verifyAllInputProvided(Map<String, Object> providedInputs,
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
}
