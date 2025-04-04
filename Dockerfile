FROM python:3.13.2

WORKDIR /src

COPY requirements.txt .
RUN apt update
RUN pip install -U pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
