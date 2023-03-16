---
description: Easily execute your model in your Python environment
---

# ML Worker

## What is ML Worker?

To leverage your Python environment with all the packages you've already installed, Giskard provides the ML Worker component.&#x20;

* It opens a secured connection between your working Python environment and the Giskard platform you've installed
* It executes the model in your working Python environment (notebook, Python IDE, etc)

{% hint style="info" %}
When Giskard is [installed](./) it comes with a default embedded ML Worker based on python 3.7. This default worker is only used by demo projects provided by Giskard.
{% endhint %}

## Starting ML Worker

1. **Install** `giskard` python library in the desired code environment:

`pip install giskard`

{% hint style="warning" %}
In case of **installation errors** related to `giskard` library, it's sometimes a good idea to remove it with:

`pip uninstall giskard`

and re-installing again
{% endhint %}

2\.  Then **start** an ML worker:

`giskard worker start`

If ML Worker manages to connect to Giskard instance, you should see the following message in the worker logs: **"Connected to Giskard server."** By default, `giskard worker start` establishes a connection to the Giskard instance installed on `localhost:40051`.&#x20;

If Giskard **is not installed locally**, please specify the IP address (and a port in case a custom port is used). For example, `giskard worker start -h 192.158.1.38`

{% hint style="warning" %}
The default port on which the Giskard server is listening for external ML Worker connections is **40051.** Make sure that this port is open on the Giskard server machine.
{% endhint %}

{% hint style="info" %}
To see all available arguments, add `--help` to the command.
{% endhint %}

## Starting ML Worker as a daemon

To start ML Worker as a daemon and let it run in the background, add `-d` argument.

`giskard worker start -d`

{% hint style="info" %}
When started from Jupyter notebook, ML Worker should be run as a daemon. Otherwise, it'll block further notebook execution, so the command to start it is:

`!giskard worker start -d`
{% endhint %}

{% hint style="info" %}
In case `giskard` command isn't available in the PATH, it's possible to start worker from running python process (jupyter kernel for example) by executing the following command:

```
import sys, os
print(os.popen(f'{sys.executable} -m giskard.cli worker start -d -h XXX').read())
```
{% endhint %}

## Running multiple ML Workers

It's possible to start multiple ML Workers, for example, to connect them to different Giskard instances. It's not possible, however, to have multiple workers that use the same python interpreter to be connected to the same Giskard instance.

If multiple workers are connected to Giskard, the **latest** one will be used.

## Stopping ML Worker

To stop a particular ML Worker that runs as a daemon `stop` command should be called with the same parameters that were used to start it.&#x20;

For example, to stop a worker started with default arguments, it's enough to call&#x20;

`giskard worker stop`

If a worker was started like&#x20;

`giskard worker start -h 11.22.33.44 -p 1234 -d`

then it can be stopped with

`giskard worker stop -h 11.22.33.44 -p 1234`

To stop all ML Workers running on a given machine:

`giskard worker stop -a`

## Having information about ML Worker in Giskard UI

Admin users can find information about an ML Worker that is currently active in Giskard on a Giskard settings page:

<figure><img src="../../.gitbook/assets/image (2) (1).png" alt=""><figcaption></figcaption></figure>

## Logs

By default, ML Worker execution logs are located in `$HOME/giskard-home/run/ml-worker.log.`

You can access the logs by executing the following command in your notebook:

```shell
!tail -f $HOME/giskard-home/run/ml-worker.log
```
