FROM ultrafunk/undetected-chromedriver

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN python -m pip install  -r requirements.txt
RUN pip install gunicorn

RUN mkdir app
WORKDIR /app
COPY . /app

CMD ["python", "-m", "gunicorn", "app:app", "-b" , ":5000", "--timeout", "1000"]