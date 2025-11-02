# spark/spark_aqi_full.py
import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from influxdb_client import InfluxDBClient, Point, WritePrecision
from collections import defaultdict

# ===============================
# CẤU HÌNH EMAIL
# ===============================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587
EMAIL_FROM  = "phuduong16112019@gmail.com"
EMAIL_PASS  = "teuj qrna ssam wyxk"
EMAIL_TO    = ["22133010@student.hcmute.edu.vn"]

# NGƯỠNG CẢNH BÁO
AQI_WARN    = 100
AQI_DANGER  = 150

# DANH SÁCH KHU VỰC
DISTRICTS = [
    "Quan1", "Quan3", "Quan4", "Quan5", "Quan6", "Quan7", "Quan8",
    "Quan10", "Quan11", "Quan12", "BinhThanh", "BinhTan", "GoVap",
    "PhuNhuan", "TanBinh", "TanPhu", "BinhChanh", "CanGio", "CuChi",
    "HocMon", "NhaBe"
]

# Buffer + Thời gian
alert_buffer = defaultdict(list)
last_summary_time = 0
SUMMARY_INTERVAL = 900  # 15 phút

print("LOG: Hệ thống AQI FULL (InfluxDB + In bảng + Email) khởi động...")

# ===============================
# InfluxDB
# ===============================
INFLUX_URL    = os.getenv("INFLUX_URL",    "http://influxdb:8086")
INFLUX_TOKEN  = os.getenv("INFLUX_TOKEN",  "admintoken")
INFLUX_ORG    = os.getenv("INFLUX_ORG",    "myorg")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "iot_data")

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api()

# ===============================
# Spark
# ===============================
spark = SparkSession.builder \
    .appName("AQI_Full_Pipeline_With_Print") \
    .config("spark.sql.shuffle.partitions", "1") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# ===============================
# Schema + Kafka
# ===============================
schema = StructType([
    StructField("fields", MapType(StringType(), DoubleType())),
    StructField("tags", MapType(StringType(), StringType())),
    StructField("timestamp", LongType())
])

raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "airquality_raw") \
    .option("startingOffsets", "latest") \
    .load()

parsed = raw.selectExpr("CAST(value AS STRING) AS json_str") \
    .select(from_json(col("json_str"), schema).alias("data")) \
    .select(
        col("data.tags")["device_id"].alias("device_id"),
        col("data.tags")["location"].alias("location"),
        col("data.fields")["CO2"].alias("CO2"),
        col("data.fields")["Humidity"].alias("Humidity"),
        col("data.fields")["NO2"].alias("NO2"),
        col("data.fields")["PM10"].alias("PM10"),
        col("data.fields")["PM2.5"].alias("PM2_5"),
        col("data.fields")["Temperature"].alias("Temperature"),
        col("data.timestamp").alias("timestamp")
    )

with_aqi = parsed.withColumn(
    "AQI", (col("PM2_5") * 0.4 + col("PM10") * 0.4 + col("NO2") * 0.2)
).filter(col("PM2_5").isNotNull() & col("PM10").isNotNull() & col("NO2").isNotNull())

with_minute = with_aqi.withColumn("minute", floor(col("timestamp") / 60) * 60)
avg_per_minute = with_minute.groupBy("location", "minute") \
    .agg(
        avg("AQI").alias("AQI_avg"),
        avg("CO2").alias("CO2_avg"),
        avg("Humidity").alias("Humidity_avg"),
        avg("NO2").alias("NO2_avg"),
        avg("PM10").alias("PM10_avg"),
        avg("PM2_5").alias("PM2_5_avg"),
        avg("Temperature").alias("Temperature_avg"),
        count("*").alias("sample_count")
    )

# ===============================
# GỬI EMAIL TỔNG HỢP 15 PHÚT
# ===============================
def send_summary_email():
    global last_summary_time
    current_time = int(time.time())
    if not alert_buffer or (current_time - last_summary_time) < SUMMARY_INTERVAL:
        return

    rows = ""
    danger_count = warn_count = 0
    for loc, alerts in alert_buffer.items():
        aqi = alerts[-1][0]
        level = "NGUY HIỂM" if aqi > AQI_DANGER else "CẢNH BÁO"
        color = "#ff6666" if aqi > AQI_DANGER else "#ffcc80"
        if aqi > AQI_DANGER: danger_count += 1
        else: warn_count += 1
        rows += f'<tr style="background:{color};"><td style="padding:8px">{loc}</td><td style="padding:8px">{aqi:.1f}</td><td style="padding:8px">{level}</td></tr>'

    if not rows:
        return

    subject = f"CẢNH BÁO AQI - TỔNG HỢP 15 PHÚT ({time.strftime('%H:%M, %d/%m/%Y')})"
    body = f"""
    <h2 style="color:#d32f2f; font-family: Arial;">CẢNH BÁO CHẤT LƯỢNG KHÔNG KHÍ</h2>
    <p style="font-family: Arial;">
      <b>Tổng: {len(alert_buffer)} khu vực vượt ngưỡng</b><br>
      <span style="color:#d32f2f">NGUY HIỂM: {danger_count}</span> | 
      <span style="color:#f57c00">CẢNH BÁO: {warn_count}</span>
    </p>

    <table border="1" style="border-collapse: collapse; width: 100%; font-family: Arial;">
      <tr style="background: #d32f2f; color: white; text-align: center;">
        <th style="padding:10px">Khu vực</th>
        <th style="padding:10px">AQI</th>
        <th style="padding:10px">Mức độ</th>
      </tr>
      {rows}
    </table>

    <hr>
    <p style="font-size: 12px; color: #777;">
      <i>Hệ thống IoT AQI Real-time - Nhóm 01</i>
    </p>
    """

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASS)
        for to_email in EMAIL_TO:
            msg['To'] = to_email
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())
            print(f"EMAIL TỔNG HỢP: ĐÃ GỬI → {to_email} | {len(alert_buffer)} khu vực")
        server.quit()
        alert_buffer.clear()
        last_summary_time = current_time
    except Exception as e:
        print(f"ERROR: Gửi email thất bại: {e}")

# ===============================
# PROCESS BATCH: IN BẢNG + GHI INFLUX + CẢNH BÁO
# ===============================
def process_batch(batch_df, batch_id):
    if batch_df.rdd.isEmpty():
        print(f"LOG: Batch {batch_id} – không có dữ liệu")
        return

    # === IN BẢNG ĐẸP TRONG LOG ===
    display_df = batch_df.withColumn("time_str", from_unixtime(col("minute")))
    print(f"\n=== BATCH {batch_id} – DỮ LIỆU TRUNG BÌNH PHÚT ===")
    display_df.select(
        "time_str",
        "location",
        col("CO2_avg").alias("CO2"),
        col("Humidity_avg").alias("Humidity"),
        col("NO2_avg").alias("NO2"),
        col("PM2_5_avg").alias("PM2.5"),
        col("PM10_avg").alias("PM10"),
        col("Temperature_avg").alias("Temperature"),
        "AQI_avg"
    ).orderBy(col("AQI_avg").desc()).show(truncate=False)

    # === GHI INFLUXDB ===
    points = []
    for r in batch_df.collect():
        p = Point("aqi_by_location") \
            .tag("location", r.location or "unknown") \
            .field("CO2", float(r.CO2_avg or 0)) \
            .field("Humidity", float(r.Humidity_avg or 0)) \
            .field("NO2", float(r.NO2_avg or 0)) \
            .field("PM10", float(r.PM10_avg or 0)) \
            .field("PM2.5", float(r.PM2_5_avg or 0)) \
            .field("Temperature", float(r.Temperature_avg or 0)) \
            .field("AQI", float(r.AQI_avg)) \
            .time(int(r.minute), WritePrecision.S)
        points.append(p)

    if points:
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
        print(f">>> Batch {batch_id}: Ghi {len(points)} điểm vào InfluxDB")

    # === LƯU VÀO BUFFER CẢNH BÁO ===
    for r in batch_df.collect():
        if r.location not in DISTRICTS:
            continue
        aqi = r.AQI_avg
        if aqi > AQI_WARN:
            level = "NGUY HIỂM" if aqi > AQI_DANGER else "CẢNH BÁO"
            alert_buffer[r.location].append((aqi, level, r.minute))

    # === GỬI EMAIL TỔNG HỢP ===
    send_summary_email()

# ===============================
# START STREAM
# ===============================
query = avg_per_minute.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("update") \
    .start()

print("LOG: Hệ thống FULL (IN BẢNG + InfluxDB + Email) đang chạy...")
query.awaitTermination()