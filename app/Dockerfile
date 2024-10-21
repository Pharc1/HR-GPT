# app/Dockerfile


FROM python:3.9-slim


RUN apt-get update && apt-get install -y curl && apt-get install -y libmagic1

WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY . .


EXPOSE 5000

COPY start.sh /start.sh
RUN chmod +x /start.sh


ENTRYPOINT ["/start.sh"]
