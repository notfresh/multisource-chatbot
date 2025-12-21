FROM python:3.8.5

ENV PYTHONUNBUFFERED 1

# 添加 Debian 阿里云镜像源
RUN echo \
deb https://mirrors.aliyun.com/debian/ buster main contrib non-free\
deb https://mirrors.aliyun.com/debian/ buster-updates main contrib non-free\
deb https://mirrors.aliyun.com/debian/ buster-backports main contrib non-free\
deb https://mirrors.aliyun.com/debian-security buster/updates main contrib non-free\
    > /etc/apt/sources.list

RUN mkdir /code
WORKDIR /code
RUN pip install pip -U  -i https://mirrors.aliyun.com/pypi/simple/  # update pip
ADD requirements.txt /code/
RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# copy the source code file to  code directory
ADD . /code/

# RUN python manage.py db upgrade

