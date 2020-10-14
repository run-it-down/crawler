FROM alpine:3.12.0

RUN apk update
RUN apk add postgresql-dev gcc python3-dev musl-dev
RUN apk add python3
RUN apk add --update py-pip
RUN pip install --upgrade pip

ADD src /src/
COPY requirements.txt .

RUN pip install -r requirements.txt

ARG DBHOST_ARG
ARG DBPORT_ARG
ARG DBUSER_ARG
ARG DBPASSWD_ARG
ARG DB_ARG
ARG RIOT_API_TOKEN

ENV DBHOST=$DBHOST_ARG
ENV DBPORT=$DBPORT_ARG
ENV DBUSER=$DBUSER_ARG
ENV DBPASSWD=$DBPASSWD_ARG
ENV DB=$DB_ARG
ENV RIOT_API_TOKEN=$RIOT_API_TOKEN
ENV PYTHONPATH "/src/"
ENTRYPOINT ["python3", "/src/main.py"]

