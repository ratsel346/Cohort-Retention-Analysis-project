import os 
from sqlalchemy import (create_engine, text, VARCHAR, DECIMAL, SMALLINT, DATE, INT)
from pathlib import Path
import pandas as pd



# Создаем путь к папке
CLEAN_DIR = Path("data/clean")
ecommerce_path = CLEAN_DIR/"ecommerce.csv"

if not ecommerce_path.exists():
    raise FileNotFoundError(
        "Файл ecommerce.csv не найден"
    )



print('Читаем очищеный файл  "ecommerce.csv"')

ecommerce = pd.read_csv(
    ecommerce_path,
    parse_dates=["transaction_date"]
)


ecommerce["transaction_id"] = ecommerce["transaction_id"].astype(str)
print("ecommerce.shape:", ecommerce.shape)




db_user = os.getenv("MYSQL_USER", "root")
db_password = os.getenv("MYSQL_PASSWORD", "MYSQL2026")
db_host = os.getenv("MYSQL_HOST", "127.0.0.1")
db_port = os.getenv("MYSQL_PORT", "3308")
db_name = os.getenv("MYSQL_NAME", "demo_project3")
print(f"\nПодкючаемся к базе данных: {db_host}:{db_port}")
print(f"Пользователь: {db_user}")
print(f"База данных: {db_name}")




server = create_engine(
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}"
)

with server.connect() as conn:
    conn.execute(text(
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
        f"CHARACTER SET utf8mb4 "
        f"COLLATE utf8mb4_unicode_ci"
    ))
    conn.commit()
print("База данных готова")




engine = create_engine(
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    f"?charset=utf8mb4"
)

ecommerce.to_sql(
    "ecommerce",
    engine,
    if_exists="replace",
    index=False,
    dtype={
        "transaction_id": INT,
        "user_id": INT,
        "transaction_date": DATE,
        "revenue": DECIMAL(12,2),
        "category": VARCHAR(100),
        "channel": VARCHAR(100),
        "is_revenue_outlier": SMALLINT,
    }
)
print("Таблица загружена")



with engine.begin() as conn:
    conn.execute(text(
        "ALTER TABLE ecommerce "
        "ADD PRIMARY KEY(transaction_id)"
    ))

check = {
   "user_count":  "SELECT COUNT(*) FROM ecommerce",
   "min_transaction_date": "SELECT MIN(transaction_date) FROM ecommerce",
   "max_transaction_date": "SELECT MAX(transaction_date) FROM ecommerce"
}
print("\nПроверка загруженных даных:")

with engine.connect() as conn:
    for name, query in check.items():
        result = conn.execute(text(query)).scalar()
        print(f"{name}:{result}")
print("\nЗагрузка в MYSQL выполнена")