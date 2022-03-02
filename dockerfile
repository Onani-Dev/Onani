FROM python
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
COPY . /Onani_Web
WORKDIR /Onani_Web
ENTRYPOINT ["./entrypoint.sh"]