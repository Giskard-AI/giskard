🌐 Run the Giskard Hub (on-premise)
===============

Complementing the `Giskard Python library <../installation_library/index.md>`_, the Giskard hub is the app that you can install either **locally**, on your **cloud instance** or on `Hugging Face Spaces <install_hfs/index.md>`_. The Giskard hub offers a bunch of features such as:

- Debugging your tests to diagnose issues
- Comparing models to decide which one to promote
- Gathering all of your team's internal tests in one place to work more efficiently
- Sharing your results and collecting business feedback from your team
- Creating more domain-specific tests based on model debugging sessions

To run the Giskard hub and use all the features mentioned above, you need to complete the following 2 steps:

- **Start the hub**: the server contains all the UI components to test, debug and compare your ML models
- **Start the worker**: the worker enables the hub to execute your model directly within your Python environment. This is important to be able to execute the model with all its dependent libraries.

1. Start the hub
^^^^^^^^^
To run the Giskard hub you need:

- A **Linux**, **macOS** machine, or **WSL2 in Windows**
- To install the Giskard **Python library**, see `here <../installation_library/index.md>`_.

You can either install and run the hub **locally** or on an **external server** (ex: cloud instance)

.. tab-set::

   .. tab-item:: Local installation

      .. hint:: **Docker requirements**: To install Giskard locally, you need a **running** ``docker``. After `installation <https://docs.docker.com/engine/install/debian/>`_ of Docker, you can run it in the background by just opening the Docker app (Mac or Windows)

         - For an easy installation of Docker you can execute:

         .. code-block:: bash

            sudo curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh

         - If you don't have the `sudo` rights to run docker, please see the Docker setup `page <https://docs.docker.com/engine/install/linux-postinstall/>`_

      To start the Giskard hub, install the Giskard Python library (see `here <../installation_library/index.md>`_) and execute the following command in your terminal:

      .. code-block:: sh

         giskard hub start

      You'll then be able to open Giskard at `http://localhost:19000/`

      .. warning::

         - Make sure to **run Docker** before starting the Giskard hub
         - If the giskard command is not found then you need first to install the Giskard Python library (see the doc section)
         - To see the available commands of the giskard hub, you can execute:


           .. code-block:: sh

              giskard hub --help


   .. tab-item:: Cloud installation

      Installing Giskard in the cloud is preferable if you want to use the **collaborative** features of Giskard: collect feedback on your model from your team, share your Quality Assurance results, save and provide all your custom tests to your team, etc.

      Since Giskard uses a TCP port: ``19000``, **make sure that the port is open** on the cloud instances where Giskard is installed. For step-by-step installation steps in the cloud, please go to the `AWS <install_aws/index/index.md>`_, `GCP <install_gcp/index.md>`_, and `Azure <install_azure/index.md>`_ installation pages.

      .. toctree::
         :maxdepth: 1

         install_aws/index
         install_gcp/index
         install_azure/index
         install_hfs/index

   .. tab-item:: Hosting in Hugging Face Spaces

      Hosting Giskard in `Hugging Face Spaces <https://huggingface.co/spaces>`_ leverages Giskard's collaboration features, as highlighted in the Cloud installation option. This option is especially useful for new users of Giskard or users entrenched in the Hugging Face ecosystem.

      .. warning:: In Hugging Face Spaces, Giskard operates within a Docker container activated by a Space. You can opt for:

        - A public Space: open to everyone (ideal for showcasing your models and their performance).
        - A private Space: restricted to your organization or yourself (facilitates internal collaboration and ensures security for your data and models).

        **For private Hugging Face Spaces, you'll need an extra token (YOUR_HF_SPACES_TOKEN) to connect the Giskard Client and ML worker.**

     If you're new to Giskard, we recommend trying this method. For comprehensive details, explore the guide on `Installation in Hugging Face Spaces <install_hfs/index.md>`_ or visit `our Hugging Face organization page <https://huggingface.co/giskardai>`_ if you're acquainted with Hugging Face Spaces.

2. Start the ML worker
^^^^^^^^^

Giskard executes your model using a worker that runs the model directly in your Python environment, with all the dependencies required by your model. You can either execute the ML worker:

- From your **local notebook** within the kernel that contains all the dependencies of your model
- From **Google Colab** within the kernel that contains all the dependencies of your model
- Or from **your terminal** within the Python environment that contains all the dependencies of your model

.. tab-set::

   .. tab-item:: From your local notebook

      To start the ML worker from your notebook, you need to start Giskard in the deamon mode by providing the API Access Key in the Settings tab of the Giskard hub (accessible via http://localhost:19000/).

      - If Giskard hub is installed **locally**, run in a cell in your notebook:

         .. code-block:: sh

            !giskard worker start -d -k YOUR_KEY

      - If Giskard hub is installed on an **external server** (for instance in AWS ec2 instance), or a public Space on Hugging Face Spaces, run the following in your notebook:

         .. code-block:: sh

            !giskard worker start -d -k YOUR_KEY -u http://ec2-13-50-XXXX.compute.amazonaws.com:19000/

      - If Giskard hub is hosted on a private Space on Hugging Face Spaces, run the following in your notebook:

         .. code-block:: sh

            !giskard worker start -d -k YOUR_KEY -u https://huggingface.co/spaces/<user-id>/<space-id> --hf-token YOUR_HF_SPACES_TOKEN

      .. hint:: To see the available commands of the worker, you can execute:

         .. code-block:: sh

            !giskard worker --help

      You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the `upload an object <../upload/index.html>`_ page.

   .. tab-item:: From Colab notebook

      To start the ML worker from your Colab notebook, you need to start Giskard in the deamon mode by providing the API Access Key in the Settings tab of the Giskard hub (accessible via http://localhost:19000/).

      - If the Giskard hub is installed **locally**:

         Run in your **local** terminal (not the the terminal from Colab):

         .. code-block:: sh

               giskard hub expose --ngrok-token <ngrok_API_token>

         Read the flowing `instructions <https://docs.giskard.ai/en/latest/cli/ngrok/index.html>`_ in order to get the
         :code:`ngrok_API_token`. Then run the below 4 lines of code in a **cell of your Colab notebook**:

         .. code-block:: sh

            %env GSK_API_KEY=YOUR_API_KEY
            !giskard worker start -d -k YOUR_KEY -u https://e840-93-23-184-184.ngrok-free.app

      - If the Giskard hub is installed on an **external** server (for instance on an AWS ec2 instance), or a public Space on Hugging Face Spaces:

         Run on a cell in Colab:

         .. code-block:: sh

               !giskard worker start -d -k YOUR_KEY -u http://ec2-13-50-XXXX.compute.amazonaws.com:19000/


      - If Giskard hub is hosted on a private Space on Hugging Face Spaces:

         Run on a cell in Colab:

         .. code-block:: sh

            !giskard worker start -d -k YOUR_KEY -u https://huggingface.co/spaces/<user-id>/<space-id> --hf-token YOUR_HF_SPACES_TOKEN

      .. hint:: To see the available commands of the worker, you can execute:

         .. code-block:: sh

            !giskard worker --help

      You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the `upload an object <../upload/index.html>`_ page.

   .. tab-item:: From your terminal

      - If Giskard hub is installed **locally**:

         Run this command **within the Python environment that contains all the dependencies of your model**:

            .. code-block:: sh

               giskard worker start -u http://localhost:19000/

            You then will be asked to provide your API Access Key. The API Access key can be found in the Settings tab of the Giskard hub (accessible via: http://localhost:19000/)

      - If Giskard hub is installed in an **external server** (for instance in AWS ec2 instance), or a public Space on Hugging Face Spaces:

         Run this command **within the Python environment that contains all the dependencies of your model**:

            .. code-block:: sh

               giskard worker start -u http://ec2-13-50-XXXX.compute.amazonaws.com:19000/

      - If Giskard hub is hosted on a private Space on Hugging Face Spaces:

         Run this command within the Python environment that contains all the dependencies of your model:

         .. code-block:: sh

            !giskard worker start -d -k YOUR_KEY -u https://huggingface.co/spaces/<user-id>/<space-id> --hf-token YOUR_HF_SPACES_TOKEN

      .. hint:: To see the available commands of the worker, you can execute:

         .. code-block:: sh

            !giskard worker --help

      You're all set to try Giskard in action. Upload your first model, dataset, test suite, or slicing & transformation functions by following the `upload an object <../upload/index.html>`_ page.
