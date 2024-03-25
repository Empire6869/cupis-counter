FROM ubuntu:22.04

# Install python3
RUN apt-get update
RUN apt-get -y install python3
RUN apt-get -y install python3-pip

# Install google chrome
RUN apt-get install -y wget
RUN wget --no-verbose -O /tmp/chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb \
  && apt install -y /tmp/chrome.deb \
  && rm /tmp/chrome.deb

# Install google chrome driver
RUN apt-get install -y unzip
RUN wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip
RUN mv chromedriver /usr/bin/chromedriver
RUN chown root:root /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver

# Prepare project
COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn
COPY . .

# Run project
CMD ["python3", "-m", "gunicorn", "app:app", "-b" , ":5000", "--timeout", "2000"]