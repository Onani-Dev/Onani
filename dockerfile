FROM python:3.10.2
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
COPY ./Onani/static /static
COPY . /onani
WORKDIR /onani
ENTRYPOINT ["./entrypoint.sh"]