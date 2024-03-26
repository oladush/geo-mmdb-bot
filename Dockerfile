FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y build-essential && apt-get -y install p7zip-full
RUN pip install --upgrade pip setuptools
RUN pip install -r requirements.txt

CMD ["python", "bot.py"]