# Giskard on Spaces

**Giskard** is an open-source testing framework dedicated for AI models, from tabular to LLMs. Giskard is composed of 
1. An open-source Python library containing a **vulnerability scan**, **testing** and **CI/CD** framework for ML models
2. The **Giskard hub**, a server app, containing a collaborative ML Testing dashboard for model **debugging** (root-cause analysis), model **comparison** & human **feedback** collection for ML.

Visit the [Giskard documentation](https://docs.giskard.ai) to learn about its features.

The Giskard hub can be easily deployed using the HF Docker Spaces. In the next sections, you'll learn to deploy your own Giskard hub and use it for testing and debugging ML models. This Giskard hub is a **self-contained application completely hosted on the Hub using Docker**. The diagram below illustrates the complete process.

<div class="flex justify-center">

</div>

## Try the Giskard Hub on demo models with the HF public space

If you want to try Giskard on some demo ML projects (and not on your own ML models), go to the Giskard Demo Hub in the **HF public space**.

<a  href="https://huggingface.co/spaces/giskardai/giskard">
    <img src="https://huggingface.co/datasets/huggingface/badges/raw/main/open-in-hf-spaces-lg.svg" />
</a>

:::{hint}
You cannot upload your private models, datasets, and projects in the demo Giskard Space. To debug & test your own model, duplicate the Space (see below).
:::

## Upload your own ML model to the Giskard Hub in HF space

To upload your own ML models, you need to deploy Giskard on Spaces. To do so, follow these steps:

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

On your first access, Giskard needs an HF access token to generate the Giskard Access Key. To do so, complete the pop up that displays when you create your first project.
[PUT THE SCREENSHOT]

Otherwise, you can also put your HF access token by going to the Giskard Settings.

## Feedback and support

If you have suggestions or need specific support, please join [Argilla Slack community](https://join.slack.com/t/rubrixworkspace/shared_invite/zt-whigkyjn-a3IUJLD7gDbTZ0rKlvcJ5g) or reach out on [Argilla's GitHub repository](https://github.com/argilla-io/argilla).
