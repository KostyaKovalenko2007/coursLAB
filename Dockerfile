FROM python:3.9-slim
COPY requirements.txt .
ARG token=local
ARG dsn=local
ARG priv_token=local
ENV token ${token}
ENV dsn ${dsn}
ENV priv_token ${priv_token}
RUN pip3 install -r requirements.txt
RUN mkdir /script
WORKDIR /script
COPY ./*.py /script/
CMD ["python3", "/script/vk_bot.py"]
