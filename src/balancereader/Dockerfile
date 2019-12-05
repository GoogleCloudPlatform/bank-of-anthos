FROM python:2.7-slim

# show python logs as they occur
ENV PYTHONUNBUFFERED=0

# get packages
WORKDIR /balancereader
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# add files into working directory
COPY . .


ENTRYPOINT ["python", "/balancereader/balance_reader.py"]
