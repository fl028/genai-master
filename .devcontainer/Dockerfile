FROM ubuntu:latest

LABEL maintainer "fl028"

#ENV http_proxy http://www-proxy:80
#ENV https_proxy http://www-proxy:80

# install utils
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y gnupg software-properties-common
RUN apt-get install -y wget 
RUN apt-get install -y curl 

# install tf
RUN wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
RUN echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
RUN apt update
RUN apt-get install -y terraform

# install az cli
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# set envs (Azure Service Principal)
ENV ARM_CLIENT_ID "..."
ENV ARM_CLIENT_SECRET "..."
ENV ARM_SUBSCRIPTION_ID "..."
ENV ARM_TENANT_ID "..."