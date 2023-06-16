# Installation in GCP

Installing Giskard in GCP enables you to inspect & test models that you created in the GCP environment (Workbench, Vertex AI, etc.). Here are the 3 steps to install Giskard in a new VM instance in GCP:

### 1. Create a Giskard VM Instance in GCP

1. Go to VM instances in Compute Engine and create a VM instance
2. In the configuration of your VM :
    1. We recommend you choose at least an `e2-standard-2` (2vCPU, 8GB memory)
    2. Choose `Allow full access to all Cloud APIs`
    3. In the firewall section, allow **HTTP** and **HTTPS** traffic
3. Connect to your VM in SSH by opening a browser window
4. Create a firewall rule to open ports `19000` and `40051` port of the Giskard instance. Here is the command line that you can execute in the terminal opened by your SSH connection:

```bash
gcloud compute firewall-rules create giskard-main --allow tcp:19000
gcloud compute firewall-rules create giskard-worker --allow tcp:40051
```

{% hint style="info" %}
Make sure you have the **proper rights** to open a port. If not contact your GCP administrator.&#x20;
{% endhint %}

{% hint style="info" %}
Creating the firewall rules can also be done **through UI** in the `VPC Network`section:

* Go to the `firewall` in `VPC Network` section of GCP
* Click on `create a firewall rule`
* In `Targets`, select `All instances in the network`
* In `Source filter`, choose `IPv4 ranges`
* In `source IPv4 ranges,` select `0.0.0.0/0`
* In `Protocols and ports`, select `Specified protocols and ports`
* Then select `TCP`, and type `19000`
* `Repeat the same steps to open port 40051`
  {% endhint %}

### 2. Install Giskard in the GCP VM

* Installation of the Giskard requirements (`git` and `docker`)

```bash
 curl -fsSL https://get.docker.com -o get-docker.sh
 sudo sh get-docker.sh
```

* Installation of Giskard

```bash
giskard server start
```

### 3. Connect to your instance and start uploading ML model

* Get the external IP address of your Giskard VM in the `VM instances` section of the `Compute Engine`
* Go to **`http://<your IP address>:19000`** in your web browser

{% hint style="info" %}
You can stop the instance and restart it when you need to save your GCP compute costs. However, note that&#x20;

* the **IP address will not necessarily be the same**. So make sure you copy it again when it's launched.
* you will need to **restart the giskard server**, by executing in the Giskard folder:

&#x20;`giskard server start`
{% endhint %}

That's it, you are now ready to use Giskard in GCP! Now you can start [uploading an artifact](docs/guide/upload/index.md)! To do that in GCP, you can use a workbench notebook, for example! &#x20;
