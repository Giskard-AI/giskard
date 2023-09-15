# Installation in AWS

### 1. Initialize EC2 instance

* In the AWS console, go to the service EC2 and select one of the following zones: N. Virginia (`us-east-1`), Paris (`eu-west-3`), or Singapore (`ap-southeast-1`)
* Launch an EC2 instance

### 2. Configure your EC2 instance

* **Application and OS image**: Select the default Ubuntu server 22.04 LTS 64-bit (x86)
* **Instance type**: We recommend you to choose at least a `t2.large` instance type (2vCPU, 8GB memory)
* **Key pair**: Choose your usual key pair. If you don't have one, go to the [Amazon document](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/create-key-pairs.html) to create the right one
* **Network settings**: You need to **open the ports `19000` and `40051` (TCP connection)** to access the Giskard frontend (port `19000`) and upload your model (port `40051`). To do so, click on `Edit` and add the following security groups:

![](<../../../assets/image_(1)_(1)_(2).png>)

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
giskard server start
```

### 4. Connect to your instance and start uploading an ML model

* **Get your IP address**: Click on the ID of the instance you just created and copy its **Public IPv4** address (or **Public IPv4 DNS**)
* Go to **`http://<your IP address>:19000`** in your web browser
* The user id is `admin` and the password is `admin`

That's it, you are now ready to use Giskard in AWS! Now you can start [uploading an artifact](docs/guide/upload/index.md)!

:::{hint}
You can stop the instance and restart it when you need to save AWS compute costs. However, note that the **IP address will not necessarily be the same**. So make sure you copy it again when it's launched
:::

