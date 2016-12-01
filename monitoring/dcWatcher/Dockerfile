FROM devopscenter/python:v2.0b1

ADD dcWatcher.py /dcWatcher/
ADD start-dcWatcher.sh /dcWatcher/
ADD stop-dcWatcher.sh /dcWatcher/
ADD commands /dcWatcher/commands/
RUN mkdir /dcWatcher/config

RUN pip install watchdog

WORKDIR /dcWatcher
CMD ["./start-dcWatcher.sh"]
