package ai.giskard.service;

import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.domain.ml.TestInput;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.TestSuiteExecution;
import ai.giskard.jobs.JobType;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.web.dto.TestCatalogDTO;
import ai.giskard.web.dto.TestDefinitionDTO;
import ai.giskard.web.dto.TestFunctionArgumentDTO;
import ai.giskard.web.dto.TestSuiteDTO;
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

import static ai.giskard.web.rest.errors.Entity.TEST;

@Service
@Transactional
@RequiredArgsConstructor
public class TestSuiteService {
    private final GiskardMapper giskardMapper;
    private final TestSuiteRepository testSuiteRepository;
    private final TestService testService;
    private final TestSuiteExecutionService testSuiteExecutionService;
    private final JobService jobService;

    public Map<String, String> getSuiteInputs(Long projectId, Long suiteId) {
        TestSuite suite = testSuiteRepository.findOneByProjectIdAndId(projectId, suiteId);
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


    @Transactional
    public UUID scheduleTestSuiteExecution(Long projectId, Long suiteId, Map<String, String> inputs) {
        TestSuite testSuite = testSuiteRepository.getById(suiteId);

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

    public TestSuiteDTO updateTestInputs(long suiteId, String testId, Map<String, String> inputs) {
        TestSuite testSuite = testSuiteRepository.getById(suiteId);

        SuiteTest test = testSuite.getTests().stream()
            .filter(t -> testId.equals(t.getTestId()))
            .findFirst().orElseThrow(() -> new EntityNotFoundException(TEST, testId));

        verifyAllInputExists(inputs, test);

        test.getTestInputs().clear();
        test.getTestInputs().addAll(inputs.entrySet().stream()
            .filter(entry -> entry.getValue() != null)
            .map(entry -> new TestInput(entry.getKey(), entry.getValue(), test))
            .toList());

        return giskardMapper.toDTO(testSuiteRepository.save(testSuite));
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

    public Path resolvedMetadataPath(Path temporaryMetadataDir, String entityName) {
        return temporaryMetadataDir.resolve(entityName.toLowerCase() + "-metadata.yaml");
    }
}
