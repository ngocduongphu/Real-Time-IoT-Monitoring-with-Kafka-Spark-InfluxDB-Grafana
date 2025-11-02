# 🌍 Real-Time IoT Air Quality Monitoring System  
### ⚡ Spark Streaming | MQTT | Kafka | InfluxDB | Grafana | Docker

> **Dự án IoT Big Data mô phỏng hệ thống giám sát chất lượng không khí thời gian thực**, sử dụng pipeline xử lý dữ liệu streaming với **Apache Spark**, **MQTT**, **Kafka**, **InfluxDB** và **Grafana**.

---

## 🎯 Mục tiêu dự án

- 🚀 Mô phỏng **hệ thống IoT thực tế** đo nồng độ bụi mịn, khí độc, nhiệt độ, độ ẩm.  
- 🔄 Xây dựng **data pipeline thời gian thực** từ sensor → MQTT → Kafka → Spark → InfluxDB.  
- 📊 Trực quan hóa dữ liệu **real-time** trên Grafana dashboard.  
- ⚠️ Tích hợp cảnh báo AQI (Air Quality Index) qua **email tự động**.  
- 🧱 Tất cả được container hóa bằng **Docker Compose**.

---

## 🧩 Kiến trúc hệ thống
## 🧩 Kiến trúc hệ thống

<p align="center">
  <img src="architecture.png" alt="System Architecture" width="750"/>
</p>
+-------------------+       +------------------+       +------------------+
|   Modbus Devices  | --->  |   MQTT Broker    | --->  |      Kafka       |
| (20 khu vực HCM)  |       | (Mosquitto)      |       | (airquality_raw) |
+-------------------+       +------------------+       +------------------+
        |                           |                           |
        |                           v                           v
        |                   +---------------+           +----------------+
        |                   |  Telegraf     | --------> | Apache Spark   |
        |                   | (MQTT→Kafka)  |           | Streaming Job  |
        |                   +---------------+           +----------------+
        |                                                       |
        |                                                       v
        |                                             +----------------+
        |                                             |   InfluxDB     |
        |                                             | (Time Series)  |
        |                                             +----------------+
        |                                                       |
        |                                                       v
        |                                             +----------------+
        |                                             |   Grafana      |
        |                                             | (Dashboard)    |
        +---------------------------------------------+----------------+

---

## 🧰 Thành phần & Công nghệ

| Thành phần | Công nghệ | Chức năng |
|-------------|------------|------------|
| **Modbus Simulator** | `Python + pymodbus` | Mô phỏng cảm biến AQI từ 20 khu vực |
| **MQTT Broker** | `Eclipse Mosquitto` | Trung gian truyền dữ liệu IoT |
| **MQTT Forwarder** | `Python + paho-mqtt` | Đọc dữ liệu Modbus → publish lên MQTT |
| **Kafka Broker** | `Confluent Kafka` | Streaming message queue |
| **Spark Streaming** | `Apache Spark 3.2.2` | Xử lý dữ liệu real-time, tính AQI, gửi cảnh báo |
| **InfluxDB 2.7** | `Time-series database` | Lưu dữ liệu cảm biến |
| **Grafana** | `Dashboard UI` | Trực quan hóa dữ liệu real-time |
| **Telegraf** | `Collector` | Chuyển tiếp dữ liệu từ MQTT → Kafka |
| **Docker Compose** | `Orchestration` | Quản lý toàn bộ hệ thống container |

---

## 📂 Cấu trúc thư mục

project/
├── modbus-simulator/              # Mô phỏng 20 cảm biến AQI
│   ├── Dockerfile
│   └── modbus_simulator.py
│
├── mqtt-forwarder/                # Đọc Modbus → publish MQTT
│   ├── Dockerfile
│   └── mqtt_forwarder.py
│
├── spark/                         # Spark Streaming xử lý + cảnh báo
│   ├── Dockerfile
│   ├── requirements.txt
│   └── spark_aqi_alert.py
│
├── mosquitto.conf                 # Cấu hình MQTT Broker
├── docker-compose.yml             # Orchestration toàn hệ thống
├── telegraf.conf                  # MQTT → Kafka bridge
└── README.md                      # Tài liệu này

---

## ⚙️ Triển khai hệ thống

### 1️⃣ Tạo mạng Docker dùng chung
docker network create mqtt-kafka-net

### 2️⃣ Khởi động toàn bộ hệ thống
docker-compose up -d

> Lúc này các container sẽ tự động chạy:  
> `modbus-simulator`, `mqtt-forwarder`, `mosquitto`, `kafka`, `spark`, `influxdb`, `grafana`.

---

## 🔍 Demo & Kiểm tra hệ thống

### Xem log Modbus Simulator (mô phỏng cảm biến)
docker logs -f modbus-simulator

### Xem log MQTT Forwarder
docker logs -f mqtt-forwarder

### Kiểm tra dữ liệu Kafka (real-time)
docker exec -it kafka bash
kafka-console-consumer --bootstrap-server localhost:19092 --topic airquality_raw --from-beginning

### Xem log Spark Streaming (xử lý & cảnh báo)
docker logs -f spark

> Spark sẽ hiển thị bảng dữ liệu trung bình từng phút, ghi dữ liệu vào InfluxDB và gửi email cảnh báo AQI.

---

## 📈 Truy cập Dashboard Grafana

- Truy cập: [http://localhost:4000](http://localhost:4000)
- Đăng nhập mặc định:
  - **Username:** `admin`
  - **Password:** `admin`
- Thêm Data Source: `InfluxDB`
  - URL: `http://influxdb:8086`
  - Token: `admintoken`
  - Org: `myorg`
  - Bucket: `iot_data`

---

## ✉️ Cảnh báo qua Email

Spark tự động gửi cảnh báo:
- **Mức cảnh báo:** AQI > 100  
- **Mức nguy hiểm:** AQI > 150  
- Email tổng hợp gửi mỗi **15 phút**, bao gồm danh sách khu vực vượt ngưỡng.

---

## 🧪 Tắt toàn bộ container

docker-compose down

---

## 🧠 Tác giả

**Nhóm 01 – Real-Time IoT Monitoring (HCMUTE)**  
📧 Email: `22133010@student.hcmute.edu.vn`  
💡 Công nghệ: Python • Spark • Kafka • InfluxDB • Docker • Grafana

---

## 🧾 Giấy phép

Distributed under the MIT License. See `LICENSE` for details.
