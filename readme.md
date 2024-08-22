# genai-master

## Overview
The repository contains the source code for my master thesis, which deals with the topic of genai.

## Setup

The repository uses the concept of Visual Studio Code Dev Containers for development. To get started, we build the container and connect the VS Code extension to the container in order to be able to perform all developments there.

### Prerequisites

1. **Visual Studio Code**: 
    - Make sure you have VS Code installed.
    - Go to the Extensions view and search for `Dev Containers` and install the extension.
2. **Docker**:
   - Install Docker Desktop if you're developing locally.
   - If you're using a remote host, ensure Docker is installed and running on the remote machine.


### Setup Base Container

1. **Azure Service Principal**: 
    - To interact with Azure resources programmatically, you'll need to create an Azure Service Principal. This is used to authenticate and authorize the Terraform deployment.
    - Set environment variables in the [Dockerfile](.devcontainer/Dockerfile#L23-L27):
      - `ENV ARM_CLIENT_ID "..."`
      - `ENV ARM_CLIENT_SECRET "..."`
      - `ENV ARM_SUBSCRIPTION_ID "..."`
      - `ENV ARM_TENANT_ID "..."`

2. **Reopen in Container**:
   - Open the Command Palette: select: `Dev Containers: Reopen in Container`
   - VS Code will start building the Docker container defined in the `.devcontainer` folder and reopen the project inside the container.

### Setup Azure Infrastructure

Use Terraform to set up the required Azure infrastructure.

1. **Apply Terraform Configuration**:
   - Navigate to the directory containing the Terraform configuration files [cd infrastructure](infrastructure/).
   - Run `terraform apply --auto-approve` to create the Azure resources.
   - Run `terraform destroy --auto-approve` to delete the Azure resources (When you are done).

### Connect to Azure Infrastructure

1. **SSH**: 
   - For the login via ssh to the cloud resources, two files are stored in the repo, which enable us to connect
      - The file `vscode_ssh_config` contains the host information for VS Code. 
      - The file `private_key.pem` contains the private ssh key.
   - Use the Remote Explorer extension to connect to the host.

2. **Clone repo**
- Run `git clone https://github.com/fl028/genai-master` to get the source code.

3. **Setup DB**:
   - If we are successfully connected to the azure vm we can test the db connection and create the tables.
   - Run `terraform output -raw mysql_password` in the terraform dev container to retrieve the db-password.
   - Run `mysql -h genai-master-db.mysql.database.azure.com -u mysqladmin -p'...' -e "SHOW DATABASES;"` to test db connection
   - Run `mysql -h genai-master-db.mysql.database.azure.com -u mysqladmin -p'...' -D data < ~/genai-master/infrastructure/create_data_db.sql` to create all tables

4. **Setup GPU**:
- check gpu: `sudo lspci | grep -i nvidia` or `sudo lshw -C display`
- install NVIDIA drivers and CUDA toolkit - this should be installed via tf (https://learn.microsoft.com/en-us/azure/virtual-machines/linux/n-series-driver-setup)
- check gpu drivers: `cat /proc/driver/nvidia/version` or `nvidia-smi`
- install NVIDIA Container Toolkit - we have to install it manually (https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#installing-with-apt)
- check gpu in container: `sudo systemctl restart docker && docker run --gpus all nvcr.io/nvidia/k8s/cuda-sample:nbody nbody -gpu -benchmark`

   
## Finetune a LLM with custom data 

We now use the generated infrastructure to fine-tune a language model with our own data (incident tickets).  Each subfolder in the code folder represents a phase.

### Ticket Transfer

The raw data is transferred from the ticket system to the database via a REST API.

1. **Reopen in Container**:
- The architecture of the vs code dev container is also used in the phases. So we open the first folder in the container. Only now we are on the azure vm.
- Open the folder: `~/genai-master/code/ticket-transfer`
- Open the Command Palette: select: `Dev Containers: Reopen in Container`
- VS Code will start building the Docker container defined in the `.devcontainer` folder and reopen the project inside the container.

2. **Setup config file**:
- To get access to the ticket api and db we have to prepare a [config.json](code\ticket-transfer\config.json)
- Fill the following content: `{
    "api-user": "...",
    "api-password": "...",
    "api-url": "...",
    "db-user": "mysqladmin",
    "db-password": "...",
    "db-host": "genai-master-db.mysql.database.azure.com",
    "db-database": "data"
}`

3. **Run python scripts**:
- Run `python check-tickets.py` to check the db (table: tickets) contents.
- Run `python get-tickets.py` to fill the db (table: tickets).


### Ticket Preperation

The raw data in the database can now be processed further. To do this, we need to clean up the ticket texts and convert them into a suitable format. The results are also saved in the database.

1. **Reopen in Container**:
- The architecture of the vs code dev container is also used in the phases. So we open the first folder in the container. Only now we are on the azure vm.
- Open the folder: `~/genai-master/code/ticket-prep`
- Open the Command Palette: select: `Dev Containers: Reopen in Container`
- VS Code will start building the Docker container defined in the `.devcontainer` folder and reopen the project inside the container.

2. **Setup config file**:
- To get access to the ticket api and db we have to prepare a [config.json](code\ticket-prep\config.json)
- Fill the following content: `{
    "db-user": "mysqladmin",
    "db-password": "...",
    "db-host": "genai-master-db.mysql.database.azure.com",
    "db-database": "data",
    "keywords": [
        "____________________",
        "------",
        "*****",
        "#####",
        ">>>",
        "<<<",
        ....
    ]
}`

3. **Run python scripts**:
- Run `python check-tickets-cleaned.py` to check the db (table: tickets_texts) contents.
- Run `python cleanup-tickets.py` to cleanup the tickets db (table: tickets_texts) contents.

### Ollama and Presidio hosting

1. **Reopen in Container**:
- Open the folder: `~/genai-master/code/ticket-presidio`
- Open the Command Palette: select: `Dev Containers: Reopen in Container`
- VS Code will start building the Docker container defined in the `.devcontainer` folder and reopen the project inside the container.

2. **Run python scripts**:
- Run `python clean-pii.py` to remove pii contents.

3. **Reopen in Container**:
- Open the folder: `~/genai-master/code/ticket-ollama`
- Open the Command Palette: select: `Dev Containers: Reopen in Container`
- VS Code will start building the Docker container defined in the `.devcontainer` folder and reopen the project inside the container.
- In this container a local llm is hosted to summarize the incident data

4. **Run python scripts**:
- Run `python check-tickets-summed.py` to check the db (table: tickets_texts) contents.
- Run `python sum-tickets.py` to sum the tickets db (table: tickets_summary) contents.

### Ticket Review (optional step and helper script)

1. **Reopen in Container**:
- Open the folder: `~/genai-master/code/ticket-review`
- Open the Command Palette: select: `Dev Containers: Reopen in Container`
- VS Code will start building the Docker container defined in the `.devcontainer` folder and reopen the project inside the container.

2. **Run python scripts**:
- Run `python review-tickets.py` to scan the database an improve the quality manually.

3. **Save data**
- Run `mysqldump -h genai-master-db.mysql.database.azure.com -u mysqladmin -p'...' --databases data > dump.sql` to dump data.
- Run `scp -i /workspaces/genai-master/infrastructure/private_key.pem azureadmin@IP:/home/azureadmin/dump.sql /workspaces/genai-master/dump.sql` to copy data to local.

### Traning

1. **Reopen in Container**:
- The architecture of the vs code dev container is also used in the phases. So we open the first folder in the container. Only now we are on the azure vm.
- Open the folder: `~/genai-master/code/train-model`
- Open the Command Palette: select: `Dev Containers: Reopen in Container`
- VS Code will start building the Docker container defined in the `.devcontainer` folder and reopen the project inside the container.

2. **Run python scripts**:
- Place the json file next to the python script (cp ticket-prep/tickets_summary.json train-model/tickets_summary.json)
- Run `python training.py` to start the training.

3. **Save Model**
Copy .gguf model to local devcontainer: `scp -i /workspaces/genai-master/infrastructure/private_key.pem azureadmin@<IP>:/home/azureadmin/genai-master/code/train-model/lora_model_gguf/unsloth.F16.gguf /workspaces/genai-master/code/train-model/lora_model_gguf/unsloth.F16.gguf`

## Deploy LLM 

1. **Reopen in Container**:
- The architecture of the vs code dev container is also used in the phases. So we open the first folder in the container. Only now we are locally again.
- Open the folder: `~/genai-master/code/deploy-ollama`
- Open the Command Palette: select: `Dev Containers: Reopen in Container`
- VS Code will start building the Docker container defined in the `.devcontainer` folder and reopen the project inside the container.

2. **Run model**:
- Place the .gguf model in code\deploy-ollama\models\time_stamp
- Edit the .modelfile
- Run `ollama create llama3.1-finetuned-time_stamp --file models/time_stamp/llama3.1-finetuned-time_stamp.modelfile`
- Run `ollama run llama3.1-finetuned-time_stamp`
- Run prompts via cli or rest api