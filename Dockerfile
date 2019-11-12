FROM python:3.7

COPY requirements.txt /src/requirements.txt

WORKDIR /src

RUN pip3 install -r requirements.txt

COPY src/ /src/

CMD ["gunicorn", "-b", "0.0.0.0:8088", "-w", "16", "server:api"]
