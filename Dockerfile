# Use an official Python 3.11 runtime as a parent image with x86 architecture
FROM --platform=linux/amd64 python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /usr/src/app
COPY common/requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN python -m pip install --target=./package -r requirements.txt

# Zip the installed packages
RUN apt-get update && \
    apt-get install -y zip && \
    cd package && \
    zip -r /app/lambda-layer.zip .

# Set the CMD to keep the container running
CMD ["tail", "-f", "/dev/null"]