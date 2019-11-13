FROM python:3.7

COPY requirements.txt /src/requirements.txt

WORKDIR /src

RUN pip3 install -r requirements.txt

# Needed for generating gifs
RUN apt-get update && apt-get install gifsicle

COPY src/ /src/

CMD ["gunicorn", "-b", "0.0.0.0:8088", "-w", "16", "server:api"]
