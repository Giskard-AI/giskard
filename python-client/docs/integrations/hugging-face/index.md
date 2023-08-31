# Giskard on Spaces

**Giskard** is an open-source testing framework dedicated for AI models, from tabular to LLMs. Giskard is composed of 
1. An open-source Python library containing a **vulnerability scan**, **testing** and **CI/CD** framework for ML models
2. The **Giskard hub**, a server app, containing a collaborative ML Testing dashboard for model **debugging** (root-cause analysis), model **comparison** & human **feedback** collection for ML.

The Giskard hub is a **self-contained application completely hosted on the Hub using Docker**. Visit the [Giskard documentation](https://docs.giskard.ai) to learn about its features.

On this page, you'll learn to deploy your own Giskard hub and use it for testing and debugging your ML models. 

<div class="flex justify-center">

</div>

## Try the Giskard Hub on demo models in 1 click

If you want to try Giskard on some demo ML projects (and not on your own ML models), go to the Giskard Demo Hub in the **HF public space**.

<a  href="https://huggingface.co/spaces/giskardai/giskard">
    <img src="https://huggingface.co/datasets/huggingface/badges/raw/main/open-in-hf-spaces-lg.svg" />
</a>

:::{hint}
You cannot upload your private models, datasets, and projects in the demo Giskard Space. To debug & test your own model, duplicate the Space (see below).
:::

## Test & debug your own ML model in the Giskard Hub using HF space

With the HF Space, you can easily test & debug your own ML models that you trained in your Python environment. This implies that you deploy a private HF space containing the Giskard Hub and upload your Python objects (such as ML models, test suites, datasets, slicing functions, or transformation functions) to your HF Space. To do so, follow these steps:

### 1. Duplicate the demo Space from Giskard
Go to Giskard HF space on https://huggingface.co/spaces/giskardai/giskard and duplicate the space (see the screenshot below).

[Duplication image](../../../assets/integrations/hfs/duplicate_this_space.png)

In the popup, you can change the **owner**, the **visibility** and the **hardware**:

![Space Duplication popup](../../../assets/integrations/hfs/paid_tier.png)

:::{hint}
**Owner and visibility**:
If you don't want to share publicly your model, keep the Space **private** and set the owner to **your organization**
**Hardware**:
We recommend you use a paid hardware to have better performance. If you choose free hardware, after 48 hours of inactivity the space will be shutdown and you will lose all the data in the Giskard Space.
:::

After clicking on `Duplicate Space` the build can take several minutes. You are now ready to upload your first model

### 2. Create a new Giskard project

[PUT THE SCREENSHOT]

### 3. Put your HF Access token

On your first access, Giskard needs an HF access token to generate the Giskard Access Key. To do so, complete the pop-up that displays when you create your first project.
[PUT THE SCREENSHOT]

Otherwise, you can also put your HF access token by going to the Giskard Settings.

### 4. Wrap your model and scan it in your Python environment

To do so follow the doc page here: https://docs.giskard.ai/en/latest/guides/scan/index.html

### 5. Upload your test suite by creating a Giskard Client for your HF Space

You can then upload the test suite resulting from your scan from your Python notebook to your HF Space. To do so you need to create a Giskard Client by copy-pasting the "Giskard client" code snippet from the Settings of the Giskard Hub to your Python notebook.

You are now ready to debug the test you just uploaded in the test tab of the Giskard Hub.

Here is the full example of the upload of a test suite to the Giskard Hub in HF Space:

.. code-block:: sh
            INSERT CODE

## Feedback and support

If you have suggestions or need specific support, please join [Giskard Discord community](https://discord.gg/ABvfpbu69R) or reach out on [Giskard's GitHub repository](https://github.com/Giskard-AI/giskard).
