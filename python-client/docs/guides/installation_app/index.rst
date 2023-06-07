🌐 Run the Giskard Server
===============

Additionally to the `Giskard Python library <../installation_library/index.md>`_, the Giskard server is the app that you can install either **locally** or on your **cloud instance**. The Giskard server offers a bunch of features such as:

- Debugging your tests to diagnose issues
- Comparing models to decide which one to promote
- Gathering all your internal tests of your team at the same place to work more efficiently
- Sharing your results and collect business feedback from your team
- Creating more domain-specific tests based on the debugging sessions

To run the Giskard server and use all the above UI features, you need to complete the following 2 steps:

- **Start the server**: the server contains all the UI components to test, debug and compare your ML models
- **Start the worker**: the worker enables the server to execute your model directly within your Python environment. This is important to be able to execute the model with all its dependent libraries.

1. Start the server
^^^^^^^^^
To run the Giskard server you need:

- A **Linux**, **macOS** machine, or **WSL2 in Windows**
- To install the Giskard Python library, see `here <../installation_library/index.md>`_.

You can either install and run the server **locally** or on an **external server** (ex: cloud instance)

.. tab-set::

   .. tab-item:: Local installation
   
      To install Giskard locally, you need: 

      - A **Linux**, **macOS** machine or **WSL2 in Windows** 
      - A running ``docker`` (`download <https://docs.docker.com/engine/install/debian/>`_) setup. For an easy installation of Docker you can execute:

         .. code-block:: bash

            sudo curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh

      To start the Giskard server, execute the following command in your terminal:

      .. code-block:: sh
      
         giskard server start --version 2.0.0b4

      You'll then be able to open Giskard at `http://localhost:19000/`

      .. warning::

         - Make sure to **run Docker** before starting the Giskard server
         - To see the available commands of the giskard server, you can execute:


           .. code-block:: sh

              giskard server --help


   .. tab-item:: Cloud installation

      Installing Giskard in the cloud is preferable if you want to use the **collaborative** features of Giskard: collect feedback on your model from your team, share your Quality Assurance results, save and provide all your custom tests to your team, etc. 

      Since Giskard uses 2 TCP ports: ``19000`` and ``40051``, **make sure that these two ports are open** on the cloud instances where Giskard is installed. For step-by-step installation steps in the cloud, please go to the `AWS <install_aws/index/index.md>`_, `GCP <install_gcp/index.md>`_, and `Azure <install_azure/index.md>`_ installation pages.

      .. toctree::
         :maxdepth: 1

         install_aws/index
         install_gcp/index
         install_azure/index

2. Start the ML worker
^^^^^^^^^

Giskard executes your model using an worker that runs directly the model in your Python environment containing all the dependencies required by your model. You can either execute the ML worker: 

- From your **local notebook** within the kernel that contains all the dependencies of your model
- From **Google Colab** within the kernel that contains all the dependencies of your model
- Or from **your terminal** within the Python environment that contains all the dependencies of your model

.. tab-set::

   .. tab-item:: From your local notebook

      To start the ML worker from your notebook, you need to start Giskard in the deamon mode by providing the token in the Settings tab of the Giskard server (accessible via http://localhost:19000/).

      - If Giskard server is installed **locally**, run in a cell in your notebook:

         .. code-block:: sh

            !giskard worker start -d -k YOUR_TOKEN

      - If Giskard server is installed on an **external server** (for instance in AWS ec2 instance), run in your notebook:

         .. code-block:: sh

            !giskard worker start -d -k YOUR_TOKEN -u http://ec2-13-50-XXXX.compute.amazonaws.com:19000/

      .. hint:: To see the available commands of the worker, you can execute:

         .. code-block:: sh

            !giskard worker --help

      You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the `upload an object <../upload/index.html>`_ page.
      
   .. tab-item:: From Colab notebook
   
      To start the ML worker from your Colab notebook, you need to start Giskard in the deamon mode by providing the token in the Settings tab of the Giskard server (accessible via http://localhost:19000/).
               
      - If the Giskard server is installed **locally**: 

         Run in your **local** terminal (not the the terminal from Colab):

         .. code-block:: sh
               
               giskard server expose
               
         Then run the below 4 lines of code in a **cell of your Colab notebook**:
            
         .. code-block:: sh
               
            %env GSK_EXTERNAL_ML_WORKER_HOST=4.tcp.ngrok.io
            %env GSK_EXTERNAL_ML_WORKER_PORT=10853
            %env GSK_API_KEY=YOUR_API_KEY
            !giskard worker start -d -u https://e840-93-23-184-184.ngrok-free.app

      - If the Giskard server is installed on an **external** server (for instance on an AWS ec2 instance):

         Run on a cell in Colab:
         
         .. code-block:: sh

               !giskard worker start -d -k YOUR_TOKEN -u http://ec2-13-50-XXXX.compute.amazonaws.com:19000/

      .. hint:: To see the available commands of the worker, you can execute:

         .. code-block:: sh

            !giskard worker --help

      You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the `upload an object <../upload/index.html>`_ page.

   .. tab-item:: From your terminal

      - If Giskard server is installed **locally**:
      
         Run this command **within the Python environment that contains all the dependencies of your model**:

            .. code-block:: sh

               giskard worker start -u http://localhost:19000/

            You then will be asked to provide your API token. The API access token can be found in the Settings tab of the Giskard server (accessible via: http://localhost:19000/)
         
      - If Giskard server is installed in an **external server** (for instance in AWS ec2 instance):

         Run this command **within the Python environment that contains all the dependencies of your model**:

            .. code-block:: sh

               giskard worker start -u http://ec2-13-50-XXXX.compute.amazonaws.com:19000/
      
      .. hint:: To see the available commands of the worker, you can execute:

         .. code-block:: sh

            !giskard worker --help

      You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the `upload an object <../upload/index.html>`_ page.
