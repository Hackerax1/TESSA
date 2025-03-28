# Use the official Python image from the Docker Hub
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install gcc and any dependencies
RUN apt-get update && apt-get install -y gcc

# Add this line to install portaudio
RUN apt-get update && apt-get install -y portaudio19-dev

# Install the dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Specify the command to run the application
CMD ["python", "app.py"]