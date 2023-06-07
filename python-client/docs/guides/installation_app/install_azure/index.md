# Installation in Azure

Installing Giskard in Azure enables you to inspect & test models that you created in the Microsoft Azure environment (ex: Azure Machine Learning, Synapse Analytics, etc.). Here are the 3 steps to install Giskard in a new VM instance in Azure:

### 1. Create a Giskard VM Instance in Azure

1. Select "Create a resource" and choose Virtual Machine
2. In the configuration of your VM, select the default configuration:
    1. Choose a Linux machine. For instance, it can be the default `Ubuntu server 20.04 LTS`
    2. We recommend you choose at least the `Standard_D2s` machine (2vCPU, 8GB memory)
    3. Enable the default SSH connection by selecting `Inbound ports: SSH (22)`
3. Create your VM instance. Make sure you downloaded the certificate file containing the private key you will need to SSH
4. On the home page, select the VM you just created by selecting `Go to Resource`
5. Go to `Settings`, `Networking`, and click on `Add inbound port rule` with the following properties:

   <figure><img src="../../.gitbook/assets/image (3) (2).png" alt=""><figcaption></figcaption></figure>
6. Connect to your VM in SSH by using the path of the **private key file** you downloaded. To do so, go to the tab `Overview`, select `Connect` and `SSH` then follow the different steps to get the right command to execute in your terminal.&#x20;

{% hint style="info" %}
For example, the terminal command line to SSH connect to your install from your computer can be:

```
sudo ssh -i /Users/bob/Downloads/Giskard2_key.cer azureuser@52.142.236.215
```

{% endhint %}

### 2. Install Giskard in the VM

* Installation of the Giskard requirements (`git` and `docker`)

```bash
 curl -fsSL https://get.docker.com -o get-docker.sh
 sudo sh get-docker.sh
```

* Installation of Giskard

```bash
giskard server start --version 2.0.0b4
```

### 3. Connect to your instance and start uploading ML model

* Get the Public IP address of your Giskard VM by clicking on the `Overview` tab
* Go to **`http://<your IP address>:19000`** in your web browser

{% hint style="info" %}
You can stop the instance and restart it when you need to save your Azure compute costs. However, note that&#x20;

* the **IP address will not necessarily be the same**. So make sure you copy it again when it's launched.
* you will need to **re-start the Giskard server**, by executing in the Giskard folder:

&#x20;`giskard server start --version 2.0.0b4`
{% endhint %}

* The user id is `admin` and the password is `admin`

That's it, you are now ready to use Giskard in Azure! Now you can start [uploading an artifact](docs/guide/upload/index.md)!&#x20;
