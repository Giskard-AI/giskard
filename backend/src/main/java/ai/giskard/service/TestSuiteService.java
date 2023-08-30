package ai.giskard.service;

import ai.giskard.domain.FunctionArgument;
import ai.giskard.domain.MLWorkerType;
import ai.giskard.domain.Project;
import ai.giskard.domain.ml.FunctionInput;
import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.TestSuiteExecution;
import ai.giskard.exception.MLWorkerIllegalReplyException;
import ai.giskard.exception.MLWorkerNotConnectedException;
import ai.giskard.jobs.JobType;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.*;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.TestSuiteExecutionRepository;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.service.ml.MLWorkerWSCommService;
import ai.giskard.service.ml.MLWorkerWSService;
import ai.giskard.utils.TransactionUtils;
import ai.giskard.web.dto.*;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.rest.errors.EntityNotFoundException;
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
@RequiredArgsConstructor
public class TestSuiteService {
    private final GiskardMapper giskardMapper;
    private final TestSuiteRepository testSuiteRepository;
    private final TestSuiteExecutionService testSuiteExecutionService;
    private final TestSuiteExecutionRepository testSuiteExecutionRepository;
    private final JobService jobService;
    private final ProjectRepository projectRepository;
    private final MLWorkerWSService mlWorkerWSService;
    private final MLWorkerWSCommService mlWorkerWSCommService;
    private final TestFunctionRepository testFunctionRepository;

    public Long saveTestSuite(String projectKey, TestSuiteDTO dto) {
        if (Strings.isBlank()) {
            throw new IllegalArgumentException("Test suite name cannot be blank");
        }

        if (dto.getProjectKey() == null) {
            dto.setProjectKey(projectKey);
        }

        TestSuite savedSuite = testSuiteRepository.save(giskardMapper.fromDTO(dto));
        return savedSuite.getId();
    }

    @Transactional(readOnly = true)
    public Map<String, RequiredInputDTO> getSuiteInputs(Long projectId, Long suiteId) {
        TestSuite suite = testSuiteRepository.findOneByProjectIdAndId(projectId, suiteId);

        Map<String, RequiredInputDTO> res = new HashMap<>();

        suite.getTests().forEach(test -> {
            ImmutableMap<String, FunctionInput> providedInputs = Maps.uniqueIndex(test.getFunctionInputs(), FunctionInput::getName);

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
    public UUID scheduleTestSuiteExecution(Long projectId, Long suiteId, List<FunctionInputDTO> inputs) {
        TestSuite testSuite = testSuiteRepository.getMandatoryById(suiteId);
        TransactionUtils.initializeTestSuite(testSuite);

        TestSuiteExecution execution = new TestSuiteExecution(testSuite);
        execution.setInputs(inputs.stream().map(giskardMapper::fromDTO).toList());

        Map<String, String> suiteInputs = getSuiteInputs(projectId, suiteId).entrySet().stream()
            .collect(Collectors.toMap(Map.Entry::getKey, e -> e.getValue().getType()));

        verifyAllInputProvided(inputs, testSuite, suiteInputs);

        MLWorkerType mlWorkerType = testSuite.getProject().getMlWorkerType();
        return jobService.undetermined(() -> {
            testSuiteExecutionService.executeScheduledTestSuite(execution, suiteInputs, false);
            testSuiteExecutionRepository.save(execution);
        }, projectId, JobType.TEST_SUITE_EXECUTION, mlWorkerType);
    }

    public TestSuiteExecution tryTestSuiteExecution(TestSuite testSuite,
                                                    Map<String, String> suiteInputs,
                                                    List<FunctionInputDTO> inputs) {
        TestSuiteExecution execution = new TestSuiteExecution(testSuite);
        execution.setInputs(inputs.stream().map(giskardMapper::fromDTO).toList());

        verifyAllInputProvided(inputs, testSuite, suiteInputs);

        testSuiteExecutionService.executeScheduledTestSuite(execution, suiteInputs, true);

        return execution;
    }

    public static void verifyAllInputProvided(List<FunctionInputDTO> providedInputs,
                                              TestSuite testSuite,
                                              Map<String, String> requiredInputs) {
        Set<String> names = providedInputs.stream().map(FunctionInputDTO::getName).collect(Collectors.toSet());

        List<String> missingInputs = requiredInputs.keySet().stream()
            .filter(requiredInput -> !names.contains(requiredInput))
            .toList();
        if (!missingInputs.isEmpty()) {
            throw new IllegalArgumentException("Inputs '%s' required to execute test suite %s"
                .formatted(String.join(", ", missingInputs), testSuite.getName()));
        }
    }

    public TestSuiteDTO updateTestInputs(long suiteId, long testId, List<FunctionInputDTO> inputs) {
        TestSuite testSuite = testSuiteRepository.getMandatoryById(suiteId);

        SuiteTest test = testSuite.getTests().stream()
            .filter(t -> testId == t.getId())
            .findFirst().orElseThrow(() -> new EntityNotFoundException(TEST_SUITE, testId));

        verifyAllInputExists(inputs, test);

        test.getFunctionInputs().clear();
        test.getFunctionInputs().addAll(inputs.stream()
            .filter(i -> i.getValue() != null)
            .map(giskardMapper::fromDTO)
            .toList());

        return giskardMapper.toDTO(testSuiteRepository.save(testSuite));
    }

    private void verifyAllInputExists(List<FunctionInputDTO> providedInputs,
                                      SuiteTest test) {
        Set<String> requiredInputs = test.getTestFunction().getArgs().stream()
            .map(FunctionArgument::getName)
            .collect(Collectors.toSet());

        List<String> nonExistingInputs = providedInputs.stream()
            .map(FunctionInputDTO::getName)
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

    public Long generateTestSuite(String projectKey, GenerateTestSuiteDTO dto) {

        Project project = projectRepository.getOneByKey(projectKey);
        MLWorkerID workerID = project.isUsingInternalWorker() ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL;
        if (mlWorkerWSService.isWorkerConnected(workerID)) {
            MLWorkerWSGenerateTestSuiteParamDTO param = MLWorkerWSGenerateTestSuiteParamDTO.builder()
                .projectKey(projectKey)
                .build();

            List<MLWorkerWSSuiteInputDTO> inputs = dto.getInputs()
                .stream()
                .map(TestSuiteService::generateSuiteInputWS)
                .toList();
            param.setInputs(inputs);

            MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(
                workerID,
                MLWorkerWSAction.GENERATE_TEST_SUITE,
                param
            );
            if (result instanceof MLWorkerWSGenerateTestSuiteDTO response) {
                TestSuite suite = new TestSuite();
                suite.setProject(project);
                suite.setName(dto.getName());
                suite.setFunctionInputs(dto.getSharedInputs().stream()
                    .map(giskardMapper::fromDTO)
                    .toList());
                suite.getTests().addAll(response.getTests().stream()
                    .map(test -> new SuiteTest(suite, test, testFunctionRepository.getMandatoryById(UUID.fromString(test.getTestUuid()))))
                    .toList());

                return testSuiteRepository.save(suite).getId();
            } else if (result instanceof MLWorkerWSErrorDTO error) {
                throw new MLWorkerIllegalReplyException(error);
            }
            throw new MLWorkerIllegalReplyException("Cannot create test suite");
        }
        throw new MLWorkerNotConnectedException(workerID);
    }

    private static MLWorkerWSSuiteInputDTO generateSuiteInputWS(GenerateTestSuiteInputDTO input) {
        MLWorkerWSSuiteInputDTO suiteInput = new MLWorkerWSSuiteInputDTO();
        suiteInput.setName(input.getName());
        suiteInput.setType(input.getType());

        if (input instanceof GenerateTestModelInputDTO generateTestModelInputDTO) {
            MLWorkerWSModelMetaDTO modelMeta = new MLWorkerWSModelMetaDTO();
            modelMeta.setModelType(generateTestModelInputDTO.getModelType());
            suiteInput.setModelMeta(modelMeta);
        } else if (input instanceof GenerateTestDatasetInputDTO generateTestDatasetInputDTO) {
            MLWorkerWSDatasetMetaDTO datasetMeta = new MLWorkerWSDatasetMetaDTO();
            datasetMeta.setTarget(generateTestDatasetInputDTO.getTarget());
            suiteInput.setDatasetMeta(datasetMeta);
        }

        return suiteInput;
    }

    public TestSuiteDTO removeSuiteTest(long suiteId, long suiteTestId) {
        TestSuite testSuite = testSuiteRepository.getMandatoryById(suiteId);

        testSuite.getTests().removeIf(suiteTest -> suiteTest.getId() == suiteTestId);

        return giskardMapper.toDTO(testSuiteRepository.save(testSuite));
    }

    public TestSuiteDTO updateTestSuite(long suiteId, TestSuiteDTO testSuiteDTO) {
        TestSuite testSuite = testSuiteRepository.getMandatoryById(suiteId);

        testSuite.setName(testSuiteDTO.getName());
        testSuite.getFunctionInputs().clear();
        testSuite.getFunctionInputs().addAll(testSuiteDTO.getFunctionInputs().stream()
            .map(giskardMapper::fromDTO)
            .toList());

        return giskardMapper.toDTO(testSuiteRepository.save(testSuite));
    }


    public void deleteTestSuite(long suiteId) {
        testSuiteRepository.deleteById(suiteId);
    }

    @Transactional(readOnly = true)
    public TestSuite getInitialized(Long suiteId) {
        TestSuite testSuite = testSuiteRepository.getMandatoryById(suiteId);
        TransactionUtils.initializeTestSuite(testSuite);
        return testSuite;
    }
}
