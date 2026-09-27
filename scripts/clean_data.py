import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns


# Создание путей к файлам
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
REPORTS_DIR = Path("reports")

# Создание папок, если их нет
CLEAN_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ОБЗОР ТАБЛИЦЫ
def print_overview(df: pd.DataFrame, name: str, key_column: str, column: str) -> None:
    """
    Печатает краткий обзор таблицы:
    - первые 15 строк
    - размер 
    - типы данных 
    - пропуски
    - полные дубликаты
    - дубликаты по ключу
    """
    print("\n" + "=" * 50)
    print(f"Обзор таблицы: {name}")
    print("=" * 50)

    print("\nПервые 15 строк:")
    print(df.head(15))

    print("\nКраткая основная информация:")
    df.info()

    print("\nКраткий статистический обзор по таблице")
    print(df.describe()) 

    print("\nДоля пропусков, %:")
    share_of_missing = df.isna().mean() * 100
    print(share_of_missing.round(2).sort_values(ascending=False))

    print("\nСумма пропусков:")
    sum_of_missing = df.isna().sum()
    print(sum_of_missing.sort_values(ascending=False))

    print("\nПолные дубликаты строк:")
    print(df.duplicated().sum())

    print(f"\nДубликаты по ключу: {key_column}")
    print(df.duplicated(subset=[key_column]).sum())

    print(f"\nУникальные значения по: {column}")
    print(df[column].value_counts())


# ОЧИСТКА ДАННЫХ
def clean_df(raw_df: pd.DataFrame):
    """
    Очищает таблицу
    """

    df = raw_df.copy()
    rows_start = len(df)

    df.columns = df.columns.str.lower().str.strip()



    # transaction_id
    df["transaction_id"] = df["transaction_id"].astype(str).str.strip()

    rows_before_t = len(df)
    df = df.drop_duplicates(subset=["transaction_id"], keep="first")
    removed_duplicates_t = rows_before_t - len(df)

    
    # user_id
    df["user_id"] = df["user_id"].astype(str).str.strip()

    df.loc[
        df["user_id"].isin(["", "nan", "NAN", "Nan", "NULL", "null", "Null", "None", "none", "NONE"]),
        "user_id"
    ] = np.nan
    df = df.dropna(subset = ["user_id"])



    # transaction_date
    END_DATE = pd.Timestamp("2026-01-01")

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], 
        errors="coerce"
    )

    df.loc[
        df["transaction_date"] > END_DATE,
        "transaction_date"
    ] = pd.NaT

    rows_before_date = len(df)
    df = df.dropna(subset = ["transaction_date"])
    removed_na_date = rows_before_date - len(df)

    

    # revenue
    # Отрицательные значения revenue удалены (30 строк, 0.06% данных)
    # В датасете отсутствует поле transaction_type, что не позволяет однозначно классифицировать эти записи как возвраты
    # Для корректного расчёта LTV и среднего чека принято решение исключить их из анализа
    # В реальном проекте необходимо уточнить у бизнеса схему учёта возвратов
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df.loc[df["revenue"] <= 0, "revenue"] = np.nan
    
    rows_before_r = len(df)
    df = df.dropna(subset=["revenue"])
    removed_na_r = rows_before_r - len(df)


    
    # category
    fixed_category = {
        "Beuty": "Beauty",
        "Hme": "Home",
        "Electonics": "Electronics",
        "Fodd": "Food",
        "clothng": "Clothing"
    }
    df["category"] = df["category"].replace(fixed_category)
    df["category"] = df["category"].astype(str).str.lower().str.strip()


    
    # channel
    df["channel"] = df["channel"].astype(str).str.lower().str.strip()



    # Проверка на выбросы
    q1 = df["revenue"].quantile(0.25)
    q3 = df["revenue"].quantile(0.75)
    iqr = q3 - q1

    upper_fence = q3 + 1.5 * iqr
    lower_fence = q1 - 1.5 * iqr

    df["is_revenue_outlier"] = (
        (df["revenue"] > upper_fence) |
        (df["revenue"] < lower_fence)
    ).astype(int)
    mistake = int(df["is_revenue_outlier"].sum())


    data_quality = {
        "table": "ecommerce_transactions",
        "start_rows": rows_start,
        "final_rows": len(df),
        "removed_dublicates": removed_duplicates_t,
        "removed_date": removed_na_date,
        "removed_revenue": removed_na_r,
        "outlier": mistake
    }
    return df, data_quality



def main():
    table_ec_t = pd.read_csv(RAW_DIR / "ecommerce_transactions.csv")
    print("Таблица загружена")

    print_overview(table_ec_t, "Ecommerce transactions", "transaction_id", "category")
    print_overview(table_ec_t, "Ecommerce transactions", "transaction_id", "channel")

    print("Построение графиков распределения выручки")
    plt.figure(figsize=(10, 6))
    sns.histplot(table_ec_t["revenue"], bins=50, kde=True)
    plt.title("Распределение выручки")
    plt.show()

    plt.figure(figsize=(10, 6))
    sns.boxplot(x=table_ec_t["revenue"])
    plt.title("Boxplot выручки")
    plt.show()

    ecommerce, ecommerce_quantity = clean_df(table_ec_t)
    print("\nОчищенная таблица")
    print(ecommerce.head())
    print("\nОтчет о качестве данных:")
    for key, value in ecommerce_quantity.items():
        print(f"  - {key}: {value}")


    quantity_report = pd.DataFrame([ecommerce_quantity])
    quantity_report.to_csv(REPORTS_DIR / "data_quantity.csv", index=False)
    print("\nОтчет о качестве данных сохранен")
    print(REPORTS_DIR / "data_quantity.csv")


    ecommerce.to_csv(CLEAN_DIR / "ecommerce.csv", index=False)

    print("\nОчищенные CSV сохранены:")
    print(CLEAN_DIR / "ecommerce.csv")

if __name__ == "__main__":
    main()



