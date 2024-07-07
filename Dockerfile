FROM python:3.12.2-slim-bullseye

WORKDIR app

COPY requirements.txt ./

RUN pip install -U -r requirements.txt

COPY . .

CMD ["python3.12", "main.py"]