If you are not working in a notebook or want to save the results for later, you can save them to an HTML file like this:

```python
scan_results.to_html("model_scan_results.html")
```

> #### 💡 Customize your scan
>
> Check our [Advanced scan usage page](https://docs.giskard.ai/en/latest/open_source/scan/advanced_scan/index.html), if
> you want to:
>   - Scan with only some **specific detectors**
>   - Make the scan **faster**

## What's next?

Your scan results may have highlighted important vulnerabilities. There are 2 important actions you can take next:

### 1. Generate a test suite from your scan results to:

* Turn the issues you found into actionable tests that you can save and reuse in further iterations

```python
test_suite = scan_results.generate_test_suite("My first test suite")

# You can run the test suite locally to verify that it reproduces the issues
test_suite.run()
```

Jump to the [test customization](https://docs.giskard.ai/en/latest/open_source/customize_tests/index.html)
and [test integration](https://docs.giskard.ai/en/latest/open_source/integrate_tests/index.html) sections to find out
everything you can do with test suites.

### 2. Upload your test suite to the Giskard Hub to:

* Compare the quality of different models and prompts to decide which one to promote
* Create more tests relevant to your use case, combining input prompts that make your model fail and custom evaluation
  criteria
* Share results, and collaborate with your team to integrate business feedback

To upload your test suite, you must have created a project on Giskard Hub and instantiated a Giskard Python client.

Then, upload your test suite like this:

```python
test_suite.upload(giskard_client, project_key)
```

[Here's a demo](https://huggingface.co/spaces/giskardai/giskard) of the Giskard Hub in action.

## Troubleshooting

If you encounter any issues, join our [Discord community](https://discord.gg/fkv7CAr3FE) and ask questions in our
#support channel.
