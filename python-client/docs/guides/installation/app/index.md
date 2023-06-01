# 🔧 Install Giskard's docker images

In order to install the Giskard server, Execute the following command in your terminal:
```sh
giskard server start --version 2.0.0
```
To see the available commands, you can execute:
```sh
giskard server --help  
```
For the full documentation, go to <project:/cli/index.rst>.

## 3. Connect the Giskard ML worker
In order to connect the ML worker, Execute the following command in your terminal:
```sh
giskard worker start -u http://localhost:19000/
```


- Install in AWS
- Install in GCP