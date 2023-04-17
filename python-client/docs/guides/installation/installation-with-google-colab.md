---
description: Easily install Giskard and connect with Google Colab
---

# Installation with Google Colab

Connecting to Giskard from Google Colab enables you to inspect & test models that you created in Colab. Here are the 4
steps to use Giskard from Google Colab:

### 1. Install and launch Giskard on your local machine

You will first need to refer to the [Installation & upgrade](./) page to install Giskard on your local machine.

### 2. Install ngrok on your local machine

Once Giskard is installed, it will be accessible to machines on your local network but not directly exposed to the
internet, where Google Colab is hosted. To do so, we recommend using [ngrok](https://ngrok.com/), a tool that provides
easy-to-use tunnels to access your local environment from the internet.

Installing ngrok is as easy as following their
documentation: [https://ngrok.com/docs/getting-started](https://ngrok.com/docs/getting-started)

### 3. Create a ngrok tunnel to your local Giskard instance

With ngrok installed, you can create a tunnel to connect to your Giskard instance. To do so, you must first create a new
file named [`ngrok.yml`](https://github.com/Giskard-AI/giskard/blob/main/scripts/ngrok.yml) on your machine. You can use
this command to do so:

```sh
curl -L https://raw.githubusercontent.com/Giskard-AI/giskard/main/scripts/ngrok.yml > ngrok.yml
```

Once the file is created, you can then use the following command, replacing `YOUR_AUTH_TOKEN` with your ngrok token
found [here](https://dashboard.ngrok.com/get-started/your-authtoken).&#x20;

<pre class="language-bash"><code class="lang-bash"><strong>ngrok start --config ngrok.yml --all --authtoken YOUR_AUTH_TOKEN
</strong></code></pre>

With this, your terminal should now look like this:

![<p>Sample <code>ngrok start</code> output</p>](<../../assets/image.png>)

### 4. Connect to your local Giskard instance

You now have a tunnel that will allow access to your local Giskard instance from your Google Collab notebook! You can
now:

* Start your ML Worker with:\
  `giskard worker start -h X.tcp.xx.ngrok.io -p XXXXX` (replacing with the URL and port from your console).
* Create your GiskardClient with:\
  `GiskardClient('https://xxxx-xx-xx-xx-xx.xx.ngrok.io')` (replacing with the URL from your console).

That's it, you are now ready to use Giskard in Colab! Now you can start [uploading a model](../upload-your-model/)!
&#x20;
