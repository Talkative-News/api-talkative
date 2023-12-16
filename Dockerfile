FROM python:3.10

# Set working directory in the container
WORKDIR /talkative_app

# Copy the entire application directory into the container
COPY . /talkative_app

RUN pip install python-dotenv

# Install Python dependencies from requirements.txt
RUN pip install -r requirements.txt
