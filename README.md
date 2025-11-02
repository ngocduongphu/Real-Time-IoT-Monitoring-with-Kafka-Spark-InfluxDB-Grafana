# Real-Time IoT Monitoring with Kafka, Spark, InfluxDB & Grafana

**Hệ thống giám sát chất lượng không khí thời gian thực tại TP.HCM**  
Sử dụng **Apache Kafka, Spark Streaming, InfluxDB, Grafana** và **Docker Compose**.

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](docker-compose.yml)
[![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/Real-Time-IoT-Monitoring-with-Kafka-Spark-InfluxDB-Grafana)](https://github.com/yourusername/Real-Time-IoT-Monitoring-with-Kafka-Spark-InfluxDB-Grafana/commits/main)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Mục tiêu
Xây dựng hệ thống **giám sát AQI thời gian thực** tại **21 quận/huyện TP.HCM** với:
- Dữ liệu cảm biến giả lập (Modbus TCP)
- Xử lý streaming bằng **Apache Spark**
- Lưu trữ chuỗi thời gian vào **InfluxDB**
- Trực quan hóa real-time trên **Grafana**
- Cảnh báo email tự động mỗi **15 phút**

---

## Tính năng chính
| Tính năng | Mô tả |
|---------|-------|
| **21 cảm biến giả lập** | Mô phỏng PM2.5, PM10, NO₂, CO₂, nhiệt độ, độ ẩm |
| **Real-time pipeline** | Độ trễ < 3 giây từ cảm biến → dashboard |
| **Cảnh báo thông minh** | Email tổng hợp mỗi 15 phút khi AQI > 100 |
| **Dashboard Grafana** | Heatmap, Line chart, Top 5 quận ô nhiễm |
| **Docker Compose** | 1 lệnh chạy toàn hệ thống |

---

## Kiến trúc hệ thống

```mermaid
graph TD
    A[Modbus Simulator<br>20 cảm biến] --> B[Mosquitto<br>MQTT]
    B --> C[Telegraf → Kafka]
    C --> D[Spark Streaming]
    D --> E[InfluxDB]
    D --> F[Email Alert]
    E --> G[Grafana Dashboard]

## Demo & Kiểm tra hệ thống
### Cài đặt nhanh

```bash
# Tạo mạng Docker riêng để các container giao tiếp với nhau
docker network create mqtt-kafka-net

# Khởi động toàn bộ hệ thống (Modbus, MQTT, Kafka, Spark, InfluxDB, Grafana) ở chế độ nền
docker-compose up -d

```bash
docker network create mqtt-kafka-net
docker-compose up -d

# 1. Xem log Modbus Simulator (cảm biến)
docker logs -f modbus-simulator

# 2. Xem log MQTT Forwarder
docker logs -f mqtt-forwarder

# 3. Xem dữ liệu Kafka (real-time)
docker exec -it kafka bash
kafka-console-consumer --bootstrap-server localhost:19092 --topic airquality_raw --from-beginning

# 4. Xem log Spark Streaming (xử lý + cảnh báo)
docker logs -f real_time_iot_monitoring_with_kafka_spark_influxdb_grafana-spark-1