FROM python:2.7

RUN mkdir -p /opt/fullpless-bot/data
WORKDIR /opt/fullpless-bot

VOLUME "/opt/fullpless-bot/data"

COPY requirements.txt /opt/fullpless-bot
RUN pip install -r /opt/fullpless-bot/requirements.txt

COPY api.py /opt/fullpless-bot
COPY core.py /opt/fullpless-bot
COPY config.py /opt/fullpless-bot

COPY db.py /opt/fullpless-bot
COPY db.sql /opt/fullpless-bot

CMD [ "python", "core.py" ]
