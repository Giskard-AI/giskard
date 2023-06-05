---
description: How to add your custom ML tests to Giskard's open-source project
---

# Contribute to Giskard

## Push your tests in the Giskard repo

* Clone the Giskard repository
* Create a GitHub branch with the base as main, starting with `test-contribution/name-of-your-branch`
* From the root of the cloned repo run `./gradlew generateProto`. This will generate the module`generated` that you will need to create your tests.
* Write your test inside one of the classes (`MetamorphicTests`, `HeuristicTests`, `PerformanceTests` or `DriftTests`) inside this [repo](https://github.com/Giskard-AI/giskard/tree/main/giskard-ml-worker/ml\_worker/testing). If your test does not fit these classes, you can also create a custom class in a new file.
* We recommend writing unit tests for your test functions: this is the way you can execute and debug your test! Unit tests should be placed in [this directory](https://github.com/Giskard-AI/giskard/tree/main/giskard-ml-worker/test).

:::{hint}
**Fixtures**

A unit test is executed with a _test model_ and _test data_ provided as fixtures.

For example, in [test\_precision](https://github.com/Giskard-AI/giskard/blob/main/giskard-ml-worker/test/test\_performance.py#L73) function, we use _german\_credit\_data_ and _german\_credit\_model_ as fixtures. If necessary, you can create your own fixtures; check [this directory](https://github.com/Giskard-AI/giskard/tree/main/giskard-ml-worker/test/fixtures) to know how.
:::

* To use this test on Giskard UI, we recommend you write the same code in the Giskard UI following these steps in our [doc](https://docs.giskard.ai/start/guides/create-tests-from-your-review/create-your-custom-test).

:::{hint}
Even if your test works, it won’t appear in Giskard's frontend, unless you re-create it as a custom test in Giskard UI.
:::

* Create a Pull Request

:::{hint}
**Example**

Let us guide you with an **example where you want to create a heuristic test function**:

* Since you are writing a heuristic test, you will select heuristic\_tests.py from the list of files under [https://github.com/Giskard-AI/giskard/tree/main/giskard-ml-worker/ml\_worker/testing](https://github.com/Giskard-AI/giskard/tree/main/giskard-ml-worker/ml\_worker/testing)
* In heuristic\_tests.py, write your code under **class HeuristicTests(AbstractTestCollection) after the existing codes**
* To write the unit test we select test\_heuristic.py under the list of files [https://github.com/Giskard-AI/giskard/tree/main/giskard-ml-worker/test](https://github.com/Giskard-AI/giskard/tree/main/giskard-ml-worker/test)
* Follow the pattern of parameterizing the inputs which helps you to test the function using different fixtures. You can read more about parameterizing unit tests here [https://docs.pytest.org/en/7.1.x/example/parametrize.html](https://docs.pytest.org/en/7.1.x/example/parametrize.html)
* If you want to create your own dataset, You can create your own fixture python file under [https://github.com/Giskard-AI/giskard/tree/main/giskard-ml-worker/test/fixtures](https://github.com/Giskard-AI/giskard/tree/main/giskard-ml-worker/test/fixtures)
* You can use [https://github.com/Giskard-AI/giskard/blob/main/giskard-ml-worker/test/fixtures/german\_credit\_scoring.py](https://github.com/Giskard-AI/giskard/blob/main/giskard-ml-worker/test/fixtures/german\_credit\_scoring.py) for your reference. Make sure you return the model, data(with target) and test\_data(without target) in the expected format. \</aside>
:::
