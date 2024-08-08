FROM nvidia/cuda:12.5.1-cudnn-runtime-ubuntu22.04

LABEL maintainer "fl028"

RUN apt-get update && apt-get upgrade -y
RUN apt install python3-pip -y
RUN alias python=/usr/bin/python3.10
RUN apt install git -y
RUN apt install wget  -y
RUN apt install pciutils -y
RUN apt install curl -y
RUN pip install pip install torch==2.3.1
RUN pip install unsloth[colab-new]
RUN pip install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes