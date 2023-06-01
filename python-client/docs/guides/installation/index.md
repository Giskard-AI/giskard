# Installation & upgrade
How to install Giskard on your machine, set up your Python backend and upgrade Giskard

:::{tip}
**Cloud installation:** To install Giskard in the **Cloud**, please go to the [**AWS**](installation-in-aws.md), [**GCP**](installation-in-gcp.md), and [**Azure**](installation-in-azure.md) installation pages&#x20;
:::

:::{note}
## Requirements

To install Giskard, you need a **Linux** or **macOS** machine or **WSL2 in Windows** with:

* Giskard uses 2 TCP ports: `19000` and `40051`. If you don't use Giskard locally (installation in the cloud for instance), **make sure that these two ports are open** on the machine where Giskard is installed
* `git (`[`download`](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)`)`
*   `docker (`[`download`](https://docs.docker.com/engine/install/debian/)`).`For an easy installation of Docker you can execute:&#x20;

    ```bash
     sudo curl -fsSL https://get.docker.com -o get-docker.sh
     sudo sh get-docker.sh
    ```
:::

Run the following commands to install Giskard on your server

```shell
git clone https://github.com/Giskard-AI/giskard.git
cd giskard
docker compose pull && docker compose up -d --force-recreate --no-build
```

:::{warning}
* If you have an error because of the rate limit (**`toomanyrequests: Rate exceeded`**), please re-execute the docker-compose command line once again.
* If`compose`is not found, you may have an older version of docker, so you'll need to use**`docker-compose`** instead of `docker compose.`Alternatively, you can also upgrade your docker version
:::

Once the docker-compose starts all the modules, you'll be able to open Giskard at [http://localhost:19000/](http://localhost:19000/)

:::{warning}
Since the backend container may take some minutes to load, please wait a bit and refresh the webpage [http://localhost:19000/](http://localhost:19000/)
:::

To log in, the default credentials are **Login: admin / Password: admin**

You're all set to try Giskard in action. Upload your first model by following the [upload-your-model](../upload-your-model/ "mention") tutorial.

## Upgrade Giskard to the latest version

In order to upgrade Giskard to the latest version, please run the following in your Giskard distribution directory

```shell
git pull
docker compose down && docker compose pull && docker compose up -d --force-recreate --no-build
```

:::{danger}
* The browser may keep using an old version of Giskard UI due to caching. If there are issues after running an upgrade try to **hard refresh** Giskard page by pressing\
  `Ctrl + Shift + R` or  `Command + Shift + R`&#x20;
* If you installed in Giskard additional **Python libraries** or a **new Python version**, you will need to reinstall them. Please refer to [configuration](../configuration.md).
:::

## Troubleshooting

:::{admonition} How can I connect to my local Giskard instance from Google Colab/other remote notebook or code environment?
:class: hint

We provide a [ngrok](https://ngrok.com/) configuration file [here](https://github.com/Giskard-AI/giskard/blob/main/scripts/ngrok.yml) which will automatically expose the required ports. You can run it using `ngrok start --config ngrok.yml --all --authtoken YOUR_AUTH_TOKEN`

1. Download the configuration file on the device hosting the Giskard instance
2. In that folder, run the command `ngrok start --config ngrok.yml --all --authtoken YOUR_AUTH_TOKEN`
3.  You should see an output similar to this: \

    [Sample "ngrok start" output](<../../assets/image_(1)_(1).png>)

4. Start your ML Worker with:\
   `giskard worker start -h X.tcp.xx.ngrok.io -p XXXXX` replacing with the URL and port from your console.
5. Create your GiskardClient with your address like this:\
   `GiskardClient('https://xxxx-xx-xx-xx-xx.xx.ngrok.io')`

:::

#### My issue isn't listed here

If you encounter any other issues, join our [**Discord**](https://discord.gg/fkv7CAr3FE) on our #support channel. Our community will help!&#x20;
