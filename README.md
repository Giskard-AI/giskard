<p align="center">
  <img width="300" alt="giskardlogo" src="frontend/src/assets/logo_full.svg">
</p>

<h3 align="center">Quality Assurance for AI</h3>
<br />
<p align="center">
    <img src="readme/inspect.png" alt="Administration panel" />
</p>

<br/>

Giskard is an open-source quality assurance platform for AI models.

- **Inspect** python models using visual interface
- Allow people leave **feedback** related to the model behaviour
- Create automatic **tests** to prevent model related bugs to appear in production

<h3 align="center">Installation</h3>

```shell
git clone https://github.com/Giskard-AI/giskard.git
cd giskard
docker-compose up -d
```

After the application is started you can access at:

http://localhost:19000

> login / password: **admin** / **admin**

<h3 align="center">Requirements</h3>

- [docker](https://docs.docker.com/get-docker/) 
- [docker-compose](https://docs.docker.com/compose/install/) 

<h3 align="center">Quick Start</h3>

You can upload models to Giskard from Jupyter notebooks or any other python environment. 
it can be done using [Giskard client library](https://docs.giskard.ai/start/guides/upload-your-model#1.-load-ai-inspector)

There's a demo python notebook available at http://localhost:18888 that can be used to upload a first model. 

<h3 align="center">Documentation</h3>

Find out more about Giskard by reading [our docs](https://docs.giskard.ai/)

<h3 align="center">Community</h3>

Join [our community](https://discord.com/invite/ABvfpbu69R) on Discord to get support and leave feedback
