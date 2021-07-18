FROM python:3.9.5-slim

ENV TZ=Europe/Berlin

WORKDIR /usr/src/app

COPY . .

RUN pip install -r requirements.txt

CMD ["python3","-u","main.py"]