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

# 确保 entrypoint.sh 有执行权限（ADD . /code/ 可能会覆盖权限）
# 同时处理可能的 Windows 行结束符问题
RUN chmod +x /code/entrypoint.sh && \
    sed -i 's/\r$//' /code/entrypoint.sh && \
    ls -la /code/entrypoint.sh

# 设置 entrypoint
ENTRYPOINT ["/code/entrypoint.sh"]

