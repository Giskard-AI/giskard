package ai.giskard.service;

import ai.giskard.domain.ml.TestInput;
import ai.giskard.domain.ml.TestSuiteExecution;
import ai.giskard.domain.ml.TestSuiteNew;
import ai.giskard.repository.TestSuiteExecutionRepository;
import ai.giskard.repository.ml.TestSuiteNewRepository;
import ai.giskard.web.dto.TestCatalogDTO;
import ai.giskard.web.dto.TestFunctionArgumentDTO;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Maps;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import static ai.giskard.utils.TransactionUtils.executeAfterTransactionCommits;
import static ai.giskard.web.rest.errors.Entity.TEST_SUITE;

@Service
@Transactional
@RequiredArgsConstructor
public class TestSuiteService {
    private final TestSuiteNewRepository testSuiteNewRepository;
    private final TestService testService;
    private final TestSuiteExecutionService testSuiteExecutionService;
    private final TestSuiteExecutionRepository testSuiteExecutionRepository;


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


    @Transactional
    public void scheduleTestSuiteExecution(Long projectId, Long suiteId, Map<String, String> inputs) {
        TestSuiteNew testSuite = testSuiteNewRepository.findById(suiteId)
            .orElseThrow(() -> new EntityNotFoundException(TEST_SUITE, suiteId));

        TestSuiteExecution execution = new TestSuiteExecution(testSuite);
        execution.setInputs(inputs.entrySet().stream()
            .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue)));
        execution.setMlWorkerType(testSuite.getProject().getMlWorkerType());

        Map<String, String> suiteInputs = getSuiteInputs(projectId, suiteId);

        verifyAllInputProvided(inputs, testSuite, suiteInputs);

        testSuiteExecutionRepository.save(execution);

        executeAfterTransactionCommits(() ->
            testSuiteExecutionService.executeScheduledTestSuite(execution.getId(), suiteInputs));
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
}
