# Installation in Hugging Face Spaces

Hugging Face Spaces could be a good start and the easiest approach to explore the functionnalities of Giskard.

Currently, Giskard also runs in a Docker container raised by a Space on Hugging Face Spaces. You can find [our demo Space](https://huggingface.co/spaces/giskardai/giskard) at Hugging Face Spaces.

To create your own instance, you can finish it in several simple clicks by duplicating this Space:

![Duplicate demo Space from Giskard](../../../assets/integrations/hfs/duplicate_this_space.png)

In the popup, you can change the owner, the visibility and the types of hardware:

![Space Duplication popup](../../../assets/integrations/hfs/paid_tier.png)

You can change the visibility of the Space to public, which makes it **accessible for everyone on the Internet**. This is nice for demonstrating the performance of your models using Giskard.

You can also keep the Space **private** and set the owner to **your organization**, which can only be accessed by you and the people under your organization. This is ideal for team collaboration, and without the risk of leakage of your datasets and models.

![Free tier Space](../../../assets/integrations/hfs/free_tier.png)

A free hardware can also be chosen, thanks to the support to the community from Hugging Face. However, it is not possible to change the sleep time.

:::{warning}
On a free hardware, after 48 hours of inactivity the space will be shutdown and you will lose all the data of Giskard.
:::

Make sure that you are all setup, and clicked on `Duplicate Space`. The Giskard instance hosted on Hugging Face Spaces can be used as described in [Upload an object to the Giskard server](../../../guides/upload/index.md), if you are using a public Space.

However, to use a private Space, there are some extra steps relating to your security and privacy.

## Notice on Private Space

To connect your Giskard Client or ML worker to your private Space in Hugging Face Spaces, you need a Space token. The token can be generated directly from your private Space, with validation of 24 hours.

The token can be acquired from instructions for ML worker connection in Giskard Settings, or the instructions to upload a test suite from demo projects.

![Input Hugging Face access token](../../../assets/integrations/hfs/input_hf_access_token.png)

On the first run, Giskard needs a Hugging Face access token to acquire a Space token from Hugging Face Spaces. The access token is valid until you manually expire it. It will only be stored in your local environment. You can create and manage them at [Hugging Face settings](https://huggingface.co/settings/tokens).

![Hugging Face settings and access token](../../../assets/integrations/hfs/where_to_create_access_token.png)

Please click on a `New token` if you do not have one.

![Generate Hugging Face access token](../../../assets/integrations/hfs/generate_token.png)

Giskard does not modify any contents or read any contents from your Hugging Face account. Set role to "read" is enough.

![Copy Hugging Face access token](../../../assets/integrations/hfs/copy_token.png)

Copy it and paste into the input field, and click on fetch.

You will see the instructions with the generated token in Giskard Client connection:

![Giskard Client instruction](../../../assets/integrations/hfs/giskard_client.png)

and in ML worker connection:

![ML Worker instruction](../../../assets/integrations/hfs/mlworker.png)

Except the Space token, you can refer [Upload an object to the Giskard server](../../../guides/upload/index.md) to upload your objects to the Giskard instance hosted on Hugging Face Spaces.
