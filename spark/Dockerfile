# FROM apache/spark-py:v3.2.2

# USER root

# WORKDIR /app
# COPY requirements.txt .
# COPY spark_to_influx.py .

# RUN pip3 install --no-cache-dir --target=/app/libs -r requirements.txt

# ENV PYTHONPATH="/app/libs:${PYTHONPATH}"

# CMD ["/opt/spark/bin/spark-submit", \
#      "--master", "local[*]", \
#      "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.2", \
#      "/app/spark_to_influx.py"]

FROM apache/spark-py:v3.2.2
USER root
WORKDIR /app
COPY requirements.txt .
COPY spark_aqi_alert.py .
RUN pip3 install --no-cache-dir --target=/app/libs -r requirements.txt
ENV PYTHONPATH="/app/libs:${PYTHONPATH}"
CMD ["/opt/spark/bin/spark-submit", "--master", "local[*]", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.2", "/app/spark_aqi_alert.py"]