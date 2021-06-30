FROM golang:1.16 AS builder

WORKDIR /go/src/github.com/hellofresh/rds_exporter
COPY . ./
RUN make

FROM python:3.7

RUN apt-get update -y \
 && apt-get install -y \
        ca-certificates \
 && rm -rf /var/cache/apt/* \
 && useradd -ms /bin/bash rds_exporter \
 && mkdir /rds_exporter \
 && chown rds_exporter:rds_exporter /rds_exporter


COPY --from=builder /go/src/github.com/hellofresh/rds_exporter/rds_exporter /rds_exporter/rds_exporter
COPY entry.py /
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

USER rds_exporter

EXPOSE 9042
ENTRYPOINT ["/usr/local/bin/python3", "/entry.py"]
