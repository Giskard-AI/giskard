package ai.giskard.utils;

import ai.giskard.domain.Callable;
import ai.giskard.domain.ml.FunctionInput;
import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.domain.ml.TestSuite;
import org.hibernate.Hibernate;

public class TransactionUtils {
    public static void initializeTestSuite(TestSuite testSuite) {
        Hibernate.initialize(testSuite.getFunctionInputs());
        Hibernate.initialize(testSuite.getTests());
        testSuite.getTests().forEach(TransactionUtils::initializeSuiteTest);
    }

    private static void initializeSuiteTest(SuiteTest suiteTest) {
        suiteTest.getFunctionInputs().forEach(TransactionUtils::initializeFunctionInput);
        Hibernate.initialize(suiteTest.getTestFunction());
        initializeCallable(suiteTest.getTestFunction());
    }

    private static void initializeFunctionInput(FunctionInput functionInput) {
        Hibernate.initialize(functionInput.getParams());
        functionInput.getParams().forEach(TransactionUtils::initializeFunctionInput);
    }

    public static void initializeCallable(Callable callable) {
        Hibernate.initialize(callable.getArgs());
    }


}
