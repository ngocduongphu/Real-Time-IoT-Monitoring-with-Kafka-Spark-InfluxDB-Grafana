# modbus-simulator/modbus_simulator.py
from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
import threading, time, struct, json, paho.mqtt.client as mqtt, random

# 20 KHU VỰC
AREAS = [
    "Quan1","Quan3","Quan4","Quan5","Quan6","Quan7","Quan8","Quan10",
    "Quan11","Quan12","BinhThanh","BinhTan","GoVap","PhuNhuan",
    "TanBinh","TanPhu","BinhChanh","CanGio","CuChi","HocMon","NhaBe"
]

MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "airquality/sensor"

# Tạo 20 slave Modbus
stores = {i: ModbusSlaveContext(hr=ModbusSequentialDataBlock(0, [0]*100)) for i in range(1, len(AREAS)+1)}
context = ModbusServerContext(slaves=stores, single=False)

# Kết nối MQTT
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
mqtt_client.loop_start()

# Float → 2 registers
def float_to_regs(f):
    b = struct.pack('>f', f)
    return [int.from_bytes(b[0:2], 'big'), int.from_bytes(b[2:4], 'big')]

# Modbus Server
def run_modbus_server():
    StartTcpServer(context, address=("0.0.0.0", 502))

threading.Thread(target=run_modbus_server, daemon=True).start()

# Data Generator + Publish
def update_and_publish():
    while True:
        for idx, area in enumerate(AREAS, start=1):
            pm25 = round(random.uniform(5, 120), 2)
            pm10 = round(pm25 * random.uniform(1.3, 2.8), 2)
            co2  = round(random.uniform(380, 1600), 2)
            no2  = round(random.uniform(5, 220), 2)
            temp = round(random.uniform(22, 38), 2)
            hum  = round(random.uniform(40, 95), 2)

            # Ghi Modbus
            store = stores[idx]
            store.setValues(3, 0,  float_to_regs(pm25))
            store.setValues(3, 2,  float_to_regs(pm10))
            store.setValues(3, 4,  float_to_regs(co2))
            store.setValues(3, 6,  float_to_regs(no2))
            store.setValues(3, 8,  float_to_regs(temp))
            store.setValues(3, 10, float_to_regs(hum))

            # Payload
            payload = {
                "device_id": f"sensor_{area}",
                "location": area,
                "PM2.5": pm25,
                "PM10": pm10,
                "CO2": co2,
                "NO2": no2,
                "Temperature": temp,
                "Humidity": hum,
                "timestamp": int(time.time())
            }

            # Publish
            topic = f"{MQTT_TOPIC_PREFIX}/{area}"
            mqtt_client.publish(topic, json.dumps(payload))

            # CHỈ IN 1 DÒNG JSON
            print(f"Published to MQTT: {json.dumps(payload, separators=(', ', ': '))}")

        time.sleep(2)

threading.Thread(target=update_and_publish, daemon=True).start()

# Giữ container chạy
while True:
    time.sleep(1)