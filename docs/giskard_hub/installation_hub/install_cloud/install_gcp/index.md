# GCP

Installing Giskard in GCP enables you to inspect & test models that you created in the GCP environment (Workbench, Vertex AI, etc.). Here are the 3 steps to install Giskard in a new VM instance in GCP:

### 1. Create a Giskard VM Instance in GCP

1. Go to VM instances in Compute Engine and create a VM instance
2. In the configuration of your VM :
    1. We recommend you choose at least an `e2-standard-2` (2vCPU, 8GB memory)
    2. Choose `Allow full access to all Cloud APIs`
    3. In the firewall section, allow **HTTP** and **HTTPS** traffic
3. Connect to your VM in SSH by opening a browser window
4. Create a firewall rule to open the `19000` port of the Giskard instance. Here is the command line that you can execute in the terminal opened by your SSH connection:

```bash
gcloud compute firewall-rules create giskard-main --allow tcp:19000
```

:::{warning}
Make sure you have the **proper rights** to open a port. If not contact your GCP administrator.&#x20;
:::

:::{note}
Creating the firewall rules can also be done **through UI** in the `VPC Network`section:


* Go to the `firewall` in `VPC Network` section of GCP
* Click on `create a firewall rule`
* In `Targets`, select `All instances in the network`
* In `Source filter`, choose `IPv4 ranges`
* In `source IPv4 ranges,` select `0.0.0.0/0`
* In `Protocols and ports`, select `Specified protocols and ports`
* Then select `TCP`, and type `19000`
:::

### 2. Install Giskard in the GCP VM

* Installation of the Giskard requirements (`git` and `docker`)

```bash
 curl -fsSL https://get.docker.com -o get-docker.sh
 sudo sh get-docker.sh
```

* Installation of Giskard

```bash
giskard hub start
```

### 3. Connect to your instance

* Get the external IP address of your Giskard VM in the `VM instances` section of the `Compute Engine`
* Go to **`http://<your IP address>:19000`** in your web browser

:::{hint}
You can stop the instance and restart it when you need to save your GCP compute costs. However, note that&#x20;

* the **IP address will not necessarily be the same**. So make sure you copy it again when it's launched.
* you will need to **restart the giskard hub**, by executing in the Giskard folder:

&#x20;`giskard hub start`
:::



### 4. Start the ML worker

Giskard executes your model using a worker that runs the model directly in **your Python environment**, with all the dependencies required by your model. You can either execute the ML worker:

- From your **local notebook** within the kernel that contains all the dependencies of your model
- From **Google Colab** within the kernel that contains all the dependencies of your model
- Or from **your terminal** within the Python environment that contains all the dependencies of your model

:::{note}
If you plan to use LLM-assisted tests or transformations, don’t forget to set the ``OPENAI_API_KEY`` environment
variable before starting the Giskard worker.
:::

:::::::{tab-set}
::::::{tab-item} From your local notebook

To start the ML worker from your notebook, run the following code in your notebook:

```
!giskard worker start -d -k YOUR_KEY -u http://<your IP address>:19000/
```

The API Access Key (`YOUR_KEY`) can be found in the Settings tab of the Giskard Hub.


> ### ⚠️ Warning
> To see the available commands of the worker, you can execute:
>```
>!giskard worker --help
>```

You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the [upload an object](../upload/index.html) page.

::::::
::::::{tab-item} From Colab notebook

To start the ML worker from your Colab notebook, run in your Colab cell:

```
!giskard worker start -d -k YOUR_KEY -u http://<your IP address>:19000/
```
The API Access Key (`YOUR_KEY`) can be found in the Settings tab of the Giskard Hub.

> ### ⚠️ Warning
> To see the available commands of the worker, you can execute:
>```
>!giskard worker --help
>```

You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the [upload an object](../upload/index.html) page.

::::::
::::::{tab-item} From your terminal

* Run the following command **within the Python environment that contains all the dependencies of your model**:

```
giskard worker start -k YOUR_KEY -u http://<your IP address>:19000/
```
The API Access Key (`YOUR_KEY`) can be found in the Settings tab of the Giskard Hub.

> ### ⚠️ Warning
> To see the available commands of the worker, you can execute:
>```
>!giskard worker --help
>```

You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the [upload an object](../upload/index.html) page.

::::::
:::::::