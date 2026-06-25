import os
import pandas as pd
import sqlite3
from google.cloud import bigquery

# Servis hesabı JSON yolu
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/mytestapp/mysite/deft-citizen-466607-q7-a0a53ceeef2a.json"

# BigQuery yapılandırması
project_id = "deft-citizen-466607-q7"
dataset_id = "inspection_dataset"
table_id = "fire_extinguishers"
full_table_id = f"{project_id}.{dataset_id}.{table_id}"

# SQLite bağlantısı ve veri çekme
conn = sqlite3.connect("/home/mytestapp/mysite/database.db")
df = pd.read_sql_query("SELECT * FROM fire_extinguishers", conn)
conn.close()

# BigQuery istemcisi
client = bigquery.Client()

# Yükleme işlemi
job = client.load_table_from_dataframe(df, full_table_id)
job.result()

print("✅ fire_extinguishers tablosu BigQuery'e başarıyla yüklendi.")
