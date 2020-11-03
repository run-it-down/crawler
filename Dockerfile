FROM alpine:3.12.0

RUN apk update
RUN apk add postgresql-dev gcc python3-dev musl-dev
RUN apk add python3
RUN apk add --update py-pip
RUN pip install --upgrade pip
RUN apk add git
RUN apk add --no-cache openssh-client

ARG DBHOST_ARG
ARG DBPORT_ARG
ARG DBUSER_ARG
ARG DBPASSWD_ARG
ARG DB_ARG
ARG SSH_PRIVATE_KEY

RUN mkdir /root/.ssh/
RUN echo $SSH_PRIVATE_KEY >> /root/.ssh/id_rsa
RUN touch /root/.ssh/known_hosts
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts
RUN chmod 400 root/.ssh/id_rsa
RUN git clone git@github.com:run-it-down/common.git /common

ADD crawler /crawler/
COPY requirements.txt .

RUN pip install -r requirements.txt

ENV DBHOST=$DBHOST_ARG
ENV DBPORT=$DBPORT_ARG
ENV DBUSER=$DBUSER_ARG
ENV DBPASSWD=$DBPASSWD_ARG
ENV DB=$DB_ARG
ENV PYTHONPATH "/crawler/:/common/"
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8002", "crawler.api", "--timeout", "600"]
