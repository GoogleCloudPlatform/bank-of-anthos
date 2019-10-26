FROM python:2.7-slim
RUN apt-get update -qqy && \
	apt-get -qqy install wget g++ && \
	rm -rf /var/lib/apt/lists/*
# show python logs as they occur
ENV PYTHONUNBUFFERED=0

# get packages
WORKDIR /ledgerwriter
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# add files into working directory
COPY . .


ENTRYPOINT ["python", "/ledgerwriter/ledger_writer.py"]
