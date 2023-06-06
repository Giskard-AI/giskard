🌐 Run the Giskard Server
===============
.. hint:: To install Giskard in the **Cloud**, please go to the `AWS <docs/guide/instal_aws/index.md>`_, `GCP <docs/guide/instal_gcp/index.md>`_, and `Azure <docs/guide/instal_azure/index.md>`_ installation pages.
   
.. toctree::
   :maxdepth: 1

   install_aws/index
   install_gcp/index
   install_azure/index

The Giskard server is the app you can install internally (locally or on your cloud instance) in addition to the `Giskard Python library <../installation_library/index.md>`_. The Giskard server offers lot's of features such as:

* Debug your tests to diagnose issues with your model
* Compare models to decide which one performs the best for your use case
* Gather all your teams internal tests in one place to work more efficiently
* Share test results with your team and collect business feedback if needed
* Create more domain-specific tests based on the debugging sessions

It can be installed locally or on an external server (cloud instance or external server) if you want to leverage all the collaborative Giskard features.

Requirements
^^^^^^^^^
To install Giskard you need a **Linux** or **macOS** machine, or **WSL2 in Windows** with:

- Giskard uses 2 TCP ports: ``19000`` and ``40051``. If you don't use Giskard locally (installation in the cloud for instance), **make sure that these two ports are open** on the machine where Giskard is installed
- ``docker`` (`download <https://docs.docker.com/engine/install/debian/>`_). For an easy installation of Docker you can execute:

   .. code-block:: bash

      sudo curl -fsSL https://get.docker.com -o get-docker.sh
      sudo sh get-docker.sh

Run the Giskard server
^^^^^^^^^

In order to start the Giskard server, execute the following command in your terminal:

.. code-block:: sh

   giskard server start --version 2.0.0

You'll then be able to open Giskard at `http://localhost:19000/ <http://localhost:19000/>`

.. warning::

   - Make sure to run Docker before starting the Giskard server
   - To see the available commands, you can execute:

     .. code-block:: sh

        giskard server --help

Now you should be set to try Giskard in action. Upload your first model, dataset or test suite by following the `upload-your-artefacts <../upload-your-model/.>`_ tutorial.

Connect the Giskard ML worker
^^^^^^^^^

Giskard executes your model directly in your Python environment through an ML worker. To connect the ML worker, execute the following command in your terminal within the Python environment that contains all the dependencies of your model:

.. code-block:: sh

   giskard worker start -u http://localhost:19000/

Troubleshooting
^^^^^^^^^

.. details::

   **How can I connect to my local Giskard instance from Google Colab/other remote notebook or code environment?**

   We provide a `ngrok <https://ngrok.com/>`_ configuration file `here <https://github.com/Giskard-AI/giskard/blob/main/scripts/ngrok.yml>`_ which will automatically expose the required ports. You can run it using ``ngrok start --config ngrok.yml --all --authtoken YOUR_AUTH_TOKEN``

   1. Download the configuration file on the device hosting the Giskard instance
   2. In that folder, run the command ``ngrok start --config ngrok.yml --all --authtoken YOUR_AUTH_TOKEN``
   3. You should see an output similar to this::

      .. figure:: ../../.gitbook/assets/image (1) (1).png
         :alt:

         Sample "ngrok start" output

   4. Start your ML Worker with:
      ``giskard worker start -h X.tcp.xx.ngrok.io -p XXXXX`` replacing with the URL and port from your console.
   5. Create your GiskardClient with your address like this:
      ``GiskardClient('https://xxxx-xx-xx-xx-xx.xx.ngrok.io')
