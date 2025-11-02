# mqtt-forwarder/mqtt_forwarder.py
import time, struct, signal, sys, json
from pymodbus.client.sync import ModbusTcpClient
import paho.mqtt.client as mqtt

MODBUS_HOST = "modbus-simulator"
MODBUS_PORT = 502
SLAVE_IDS = list(range(1, 22))

MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "airquality/sensor"

POLL_INTERVAL = 2

AREAS = [
    "Quan1","Quan3","Quan4","Quan5","Quan6","Quan7","Quan8","Quan10",
    "Quan11","Quan12","BinhThanh","BinhTan","GoVap","PhuNhuan",
    "TanBinh","TanPhu","BinhChanh","CanGio","CuChi","HocMon","NhaBe"
]

def regs_to_float(high, low):
    try:
        b = high.to_bytes(2, 'big') + low.to_bytes(2, 'big')
        return struct.unpack('>f', b)[0]
    except:
        return None

# Kết nối Modbus
modbus_client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
if not modbus_client.connect():
    print("ERROR: Cannot connect to Modbus")
    sys.exit(1)

# Kết nối MQTT
mqtt_client = mqtt.Client()
connected = False
for i in range(10):
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        connected = True
        break
    except Exception as e:
        time.sleep(5)
if not connected:
    print("ERROR: MQTT connection failed")
    sys.exit(1)

stop = False
def on_signal(sig, frame):
    global stop
    stop = True
signal.signal(signal.SIGINT, on_signal)
signal.signal(signal.SIGTERM, on_signal)

while not stop:
    for slave_id, area in zip(SLAVE_IDS, AREAS):
        try:
            rr = modbus_client.read_holding_registers(address=0, count=12, unit=slave_id)
            if rr.isError():
                continue

            regs = rr.registers
            pm25 = regs_to_float(regs[0], regs[1])
            pm10 = regs_to_float(regs[2], regs[3])
            co2  = regs_to_float(regs[4], regs[5])
            no2  = regs_to_float(regs[6], regs[7])
            temp = regs_to_float(regs[8], regs[9])
            hum  = regs_to_float(regs[10], regs[11])

            if None in (pm25, pm10, co2, no2, temp, hum):
                continue

            payload = {
                "device_id": f"sensor_{area}",
                "location": area,
                "PM2.5": round(pm25, 2),
                "PM10": round(pm10, 2),
                "CO2": round(co2, 2),
                "NO2": round(no2, 2),
                "Temperature": round(temp, 2),
                "Humidity": round(hum, 2),
                "timestamp": int(time.time())
            }

            topic = f"{MQTT_TOPIC_PREFIX}/{area}"
            mqtt_client.publish(topic, json.dumps(payload))

            # CHỈ IN 1 DÒNG JSON
            print(f"Published to MQTT: {json.dumps(payload, separators=(', ', ': '))}")

        except Exception as e:
            pass  # Bỏ qua lỗi, không in

    time.sleep(POLL_INTERVAL)

modbus_client.close()
mqtt_client.disconnect()