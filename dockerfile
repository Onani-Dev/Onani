FROM python
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
COPY ./Onani/static /static
COPY . /onani
WORKDIR /onani
ENTRYPOINT ["./entrypoint.sh"]