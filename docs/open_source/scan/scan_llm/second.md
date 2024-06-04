If you are not working in a notebook or want to save the results for later, you can save them to an HTML file like this:

```python
scan_results.to_html("model_scan_results.html")
```

> #### 💡 Customize your scan
>
> Check our [Advanced scan usage page](https://docs.giskard.ai/en/stable/open_source/scan/advanced_scan/index.html), if
> you want to:
>
> - Scan with only some **specific detectors**
> - Make the scan **faster**

## What's next?

Your scan results may have highlighted important vulnerabilities. There are 2 important actions you can take next:

### 1. Generate a test suite from your scan results to:

- Turn the issues you found into actionable tests that you can save and reuse in further iterations

```python
test_suite = scan_results.generate_test_suite("My first test suite")

# You can run the test suite locally to verify that it reproduces the issues
test_suite.run()
```

Jump to the [test customization](https://docs.giskard.ai/en/stable/open_source/customize_tests/index.html)
and [test integration](https://docs.giskard.ai/en/stable/open_source/integrate_tests/index.html) sections to find out
everything you can do with test suites.

### 2. Run the test suite with a different model:

```python
# wrap a different model
giskard_model_2 = giskard.Model(...)

# run the test suite with the new model
test_suite.run(model=giskard_model_2)
```

Check the [test suite documentation](https://docs.giskard.ai/en/stable/reference/suite/index.html#giskard.Suite) to learn more.

## Troubleshooting

If you encounter any issues, join our [Discord community](https://discord.gg/fkv7CAr3FE) and ask questions in our #support channel.
