package ai.giskard.service;

import ai.giskard.domain.Project;
import ai.giskard.domain.TestFunctionArgument;
import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.domain.ml.TestInput;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.TestSuiteExecution;
import ai.giskard.jobs.JobType;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.*;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.worker.*;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Maps;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.file.Path;
import java.util.*;
import java.util.stream.Collectors;

import static ai.giskard.web.rest.errors.Entity.TEST_SUITE;


@Service
@Transactional
@RequiredArgsConstructor
public class TestSuiteService {
    private final GiskardMapper giskardMapper;
    private final TestSuiteRepository testSuiteRepository;
    private final TestSuiteExecutionService testSuiteExecutionService;
    private final JobService jobService;
    private final ProjectRepository projectRepository;
    private final MLWorkerService mlWorkerService;
    private final TestFunctionRepository testFunctionRepository;

    public Map<String, RequiredInputDTO> getSuiteInputs(Long projectId, Long suiteId) {
        TestSuite suite = testSuiteRepository.findOneByProjectIdAndId(projectId, suiteId);

        Map<String, RequiredInputDTO> res = new HashMap<>();

        suite.getTests().forEach(test -> {
            ImmutableMap<String, TestInput> providedInputs = Maps.uniqueIndex(test.getTestInputs(), TestInput::getName);

            test.getTestFunction().getArgs().stream()
                .filter(a -> !a.isOptional())
                .forEach(a -> {
                    String name = null;
                    boolean isShared = false;
                    if (!providedInputs.containsKey(a.getName())) {
                        name = a.getName();
                    } else if (providedInputs.get(a.getName()).isAlias()) {
                        name = providedInputs.get(a.getName()).getValue();
                        isShared = true;
                    }
                    if (name != null) {
                        if (res.containsKey(name) && !a.getType().equals(res.get(name).getType())) {
                            throw new IllegalArgumentException("Variable with name %s is declared as %s and %s at the same time".formatted(a.getName(), res.get(a.getName()), a.getType()));
                        } else if (res.containsKey(name)) {
                            res.get(name).setSharedInput(isShared || res.get(name).isSharedInput());
                        } else {
                            res.put(name, new RequiredInputDTO(a.getType(), isShared));
                        }
                    }
                });
        });

        return res;
    }


    @Transactional
    public UUID scheduleTestSuiteExecution(Long projectId, Long suiteId, Map<String, String> inputs) {
        TestSuite testSuite = testSuiteRepository.getById(suiteId);

        TestSuiteExecution execution = new TestSuiteExecution(testSuite);
        execution.setInputs(inputs.entrySet().stream()
            .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue)));

        Map<String, String> suiteInputs = getSuiteInputs(projectId, suiteId).entrySet().stream()
            .collect(Collectors.toMap(Map.Entry::getKey, e -> e.getValue().getType()));

        verifyAllInputProvided(inputs, testSuite, suiteInputs);

        return jobService.undetermined(() ->
                testSuiteExecutionService.executeScheduledTestSuite(execution, suiteInputs), projectId, JobType.TEST_SUITE_EXECUTION,
            testSuite.getProject().getMlWorkerType());
    }

    private static void verifyAllInputProvided(Map<String, String> providedInputs,
                                               TestSuite testSuite,
                                               Map<String, String> requiredInputs) {
        List<String> missingInputs = requiredInputs.keySet().stream()
            .filter(requiredInput -> !providedInputs.containsKey(requiredInput))
            .toList();
        if (!missingInputs.isEmpty()) {
            throw new IllegalArgumentException("Inputs '%s' required to execute test suite %s"
                .formatted(String.join(", ", missingInputs), testSuite.getName()));
        }
    }

    public TestSuiteDTO updateTestInputs(long suiteId, long testId, List<TestInputDTO> inputs) {
        TestSuite testSuite = testSuiteRepository.getById(suiteId);

        SuiteTest test = testSuite.getTests().stream()
                .filter(t -> testId == t.getId())
                .findFirst().orElseThrow(() -> new EntityNotFoundException(TEST_SUITE, testId));

        verifyAllInputExists(inputs, test);

        test.getTestInputs().clear();
        test.getTestInputs().addAll(inputs.stream()
            .filter(i -> i.getValue() != null)
            .map(giskardMapper::fromDTO)
            .toList());
        test.getTestInputs().forEach(input -> input.setTest(test));

        return giskardMapper.toDTO(testSuiteRepository.save(testSuite));
    }

    private void verifyAllInputExists(List<TestInputDTO> providedInputs,
                                      SuiteTest test) {
        Set<String> requiredInputs = test.getTestFunction().getArgs().stream()
            .map(TestFunctionArgument::getName)
            .collect(Collectors.toSet());

        List<String> nonExistingInputs = providedInputs.stream()
            .map(TestInputDTO::getName)
            .filter(providedInput -> !requiredInputs.contains(providedInput))
            .toList();

        if (!nonExistingInputs.isEmpty()) {
            throw new IllegalArgumentException("Inputs '%s' does not exists for test %s"
                .formatted(String.join(", ", nonExistingInputs),
                    Objects.requireNonNullElse(test.getTestFunction().getDisplayName(), test.getTestFunction().getName())));
        }
    }

    public Path resolvedMetadataPath(Path temporaryMetadataDir, String entityName) {
        return temporaryMetadataDir.resolve(entityName.toLowerCase() + "-metadata.yaml");
    }

    public TestSuite addTestToSuite(long suiteId, SuiteTestDTO suiteTestDTO) {
        TestSuite suite = testSuiteRepository.findById(suiteId)
            .orElseThrow(() -> new EntityNotFoundException(TEST_SUITE, suiteId));

        SuiteTest suiteTest = giskardMapper.fromDTO(suiteTestDTO);
        suiteTest.setSuite(suite);
        suite.getTests().add(suiteTest);

        return testSuiteRepository.save(suite);
    }

    @Transactional
    public Long generateTestSuite(String projectKey, GenerateTestSuiteDTO dto) {

        Project project = projectRepository.getOneByKey(projectKey);
        try (MLWorkerClient client = mlWorkerService.createClient(project.isUsingInternalWorker())) {
            GenerateTestSuiteRequest.Builder request = GenerateTestSuiteRequest.newBuilder()
                .setProjectKey(projectKey);

            request.addAllInputs(dto.getInputs()
                .stream()
                .map(TestSuiteService::generateSuiteInput)
                .toList());

            GenerateTestSuiteResponse response = client.getBlockingStub().generateTestSuite(request.build());

            TestSuite suite = new TestSuite();
            suite.setProject(project);
            suite.setName(dto.getName());
            suite.setTestInputs(dto.getSharedInputs().stream()
                .map(giskardMapper::fromDTO)
                .toList());
            suite.getTestInputs().forEach(input -> input.setSuite(suite));
            suite.getTests().addAll(response.getTestsList().stream()
                .map(test -> new SuiteTest(suite, test, testFunctionRepository.getById(UUID.fromString(test.getTestUuid()))))
                .toList());

            return testSuiteRepository.save(suite).getId();
        }
    }

    private static SuiteInput generateSuiteInput(GenerateTestSuiteInputDTO input) {
        SuiteInput.Builder builder = SuiteInput.newBuilder()
            .setName(input.getName())
            .setType(input.getType());

        if (input instanceof GenerateTestModelInputDTO generateTestModelInputDTO) {
            builder.setModelMeta(ModelMeta.newBuilder()
                    .setModelType(generateTestModelInputDTO.getModelType())
                    .build());
        } else if (input instanceof GenerateTestDatasetInputDTO generateTestDatasetInputDTO) {
            builder.setDatasetMeta(DatasetMeta.newBuilder()
                    .setTarget(generateTestDatasetInputDTO.getTarget())
                    .build());
        }

        return builder.build();
    }

    public TestSuiteDTO removeSuiteTest(long suiteId, long suiteTestId) {
        TestSuite testSuite = testSuiteRepository.getById(suiteId);

        testSuite.getTests().removeIf(suiteTest -> suiteTest.getId() == suiteTestId);

        return giskardMapper.toDTO(testSuiteRepository.save(testSuite));
    }

    @Transactional
    public TestSuiteDTO updateTestSuite(long suiteId, TestSuiteDTO testSuiteDTO) {
        TestSuite testSuite = testSuiteRepository.getById(suiteId);

        testSuite.setName(testSuiteDTO.getName());
        testSuite.getTestInputs().clear();
        testSuite.getTestInputs().addAll(testSuiteDTO.getTestInputs().stream()
            .map(giskardMapper::fromDTO)
            .toList());
        testSuite.getTestInputs().forEach(input -> input.setSuite(testSuite));

        return giskardMapper.toDTO(testSuiteRepository.save(testSuite));
    }
}
