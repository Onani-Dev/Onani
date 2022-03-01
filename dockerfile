FROM python
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
COPY . /Onani_Web
WORKDIR /Onani_Web
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:5000","-w", "10", "--threads", "10",  "run:app"]
#RUN python init_db.py