FROM python:3.12-slim 
#使用python基础镜像
WORKDIR /python
#创建在镜像/容器内代码的地址
COPY . .
#将物理电脑这个文件夹内的所有代码复制到镜像的workspace内
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
#安装代码运行所需环境
# RUN pip install opencv-python-headless -i https://pypi.tuna.tsinghua.edu.cn/simple
#yolo系列会报一个有关so的错误，下载这个即可
CMD ["python3","main.py"]
#创建命令