# AWS

### 1. Initialize EC2 instance

* In the AWS console, go to the service EC2 and select one of the following zones: N. Virginia (`us-east-1`), Paris (`eu-west-3`), or Singapore (`ap-southeast-1`)
* Launch an EC2 instance

### 2. Configure your EC2 instance

* **Application and OS image**: Select the default Ubuntu server 22.04 LTS 64-bit (x86)
* **Instance type**: We recommend you to choose at least a `t2.large` instance type (2vCPU, 8GB memory)
* **Key pair**: Choose your usual key pair. If you don't have one, go to the [Amazon document](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/create-key-pairs.html) to create the right one
* **Network settings**: You need to **open the port `19000` to access the Giskard frontend and upload your model. To do so, click on `Edit` and add the following security groups:

![](../../../../assets/image_(1)_(1)_(2).png)

* **Storage**: Choose a minimum of 30 Gigs of SSD (this will mainly depend on the size of your datasets)

### 3. Launch the instance and install Giskard

* Click on Launch instance to create the instance
* Connect in SSH to your instance. You can for example use the `EC2 Instance connect` to open a terminal directly in your AWS platform
* Installation of the Giskard requirements (`docker`)

```bash
 curl -fsSL https://get.docker.com -o get-docker.sh
 sudo sh get-docker.sh
```

* Installation of Giskard

```bash
giskard hub start
```

### 4. Connect to your instance
* **Get your IP address**: Click on the ID of the instance you just created and copy its **Public IPv4** address (or **Public IPv4 DNS**)
* Go to **`http://<your IP address>:19000`** in your web browser. For instance, `http://ec2-13-50-XXXX.compute.amazonaws.com:19000`
* The user id is `admin` and the password is `admin`

:::{hint}
You can stop the instance and restart it when you need to save AWS compute costs. However, note that the **IP address will not necessarily be the same**. So make sure you copy it again when it's launched
:::

### 5. Start the ML worker

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