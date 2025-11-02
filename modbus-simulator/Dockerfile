FROM python:3.11-slim

WORKDIR /app
COPY modbus_simulator.py .

RUN pip install pymodbus==2.5.3 paho-mqtt==1.6.1

CMD ["python", "modbus_simulator.py"]