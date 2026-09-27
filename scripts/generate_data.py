"""
Скрипт для генерации реалистичных данных для когортного анализа
Создает ~50 000 транзакций для ~5 000 пользователей
Включает намеренные "загрязнения" для практики очистки данных
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Для воспроизводимости результатов
np.random.seed(42)
random.seed(42)

# ==================== КОНФИГУРАЦИЯ ====================
NUM_USERS = 5000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 8, 31)
OUTPUT_PATH = 'data/raw/ecommerce_transactions.csv'

# Каналы привлечения и их веса
CHANNELS = ['organic', 'paid_search', 'social', 'email', 'referral']
CHANNEL_WEIGHTS = [0.30, 0.25, 0.20, 0.15, 0.10]

# Категории товаров
CATEGORIES = ['Electronics', 'Clothing', 'Home', 'Food', 'Beauty']
CATEGORY_AVG_PRICES = {
    'Electronics': 300,
    'Clothing': 80,
    'Home': 150,
    'Food': 40,
    'Beauty': 60
}

# ==================== ГЕНЕРАЦИЯ ПОЛЬЗОВАТЕЛЕЙ ====================
def generate_users():
    """Генерирует пользователей с датами первой покупки (когортами)"""
    users = []
    
    # Распределение по когортам (месяцам)
    cohort_probs = [0.08, 0.07, 0.07, 0.06, 0.06, 0.06,
                    0.06, 0.06, 0.05, 0.05, 0.05, 0.05,
                    0.05, 0.04, 0.04, 0.04, 0.04, 0.04,
                    0.02, 0.01]
    
    # Генерируем все месяцы сразу (векторизованно — быстрее)
    months_offsets = np.random.choice(range(20), size=NUM_USERS, p=cohort_probs)
    channels = np.random.choice(CHANNELS, size=NUM_USERS, p=CHANNEL_WEIGHTS)
    
    for i in range(NUM_USERS):
        # FIX: явное преобразование numpy.int64 → Python int
        months_offset = int(months_offsets[i])
        first_purchase_date = START_DATE + timedelta(days=months_offset * 30)
        
        users.append({
            'user_id': i + 1,
            'first_purchase_date': first_purchase_date,
            'channel': channels[i]
        })
    
    return pd.DataFrame(users)

# ==================== ГЕНЕРАЦИЯ ТРАНЗАКЦИЙ ====================
def generate_transactions(users_df):
    """Генерирует транзакции для каждого пользователя"""
    transactions = []
    transaction_id = 1
    
    for _, user in users_df.iterrows():
        user_id = int(user['user_id'])
        first_date = user['first_purchase_date']
        channel = user['channel']
        
        # Определяем количество транзакций (зависит от канала)
        if channel == 'email':
            num_transactions = int(np.random.poisson(8)) + 1
        elif channel == 'paid_search':
            num_transactions = int(np.random.poisson(3)) + 1
        else:
            num_transactions = int(np.random.poisson(5)) + 1
        
        # ~15% пользователей делают только одну покупку
        if np.random.random() < 0.15:
            num_transactions = 1
        
        # Генерируем даты транзакций
        last_category = None
        for i in range(num_transactions):
            if i == 0:
                trans_date = first_date
            else:
                # FIX: явное преобразование в Python int
                days_offset = int(np.random.exponential(scale=30) * i)
                trans_date = first_date + timedelta(days=days_offset)
                
                if trans_date > END_DATE:
                    break
            
            # Выбираем категорию
            if i == 0:
                category = np.random.choice(CATEGORIES)
            else:
                if np.random.random() < 0.6 and last_category is not None:
                    category = last_category
                else:
                    category = np.random.choice(CATEGORIES)
            
            last_category = category
            
            # Генерируем revenue
            avg_price = CATEGORY_AVG_PRICES[category]
            revenue = float(max(10, np.random.normal(avg_price, avg_price * 0.3)))
            
            # Сезонность (ноябрь-декабрь: +30%)
            if trans_date.month in [11, 12]:
                revenue *= 1.3
            
            transactions.append({
                'transaction_id': transaction_id,
                'user_id': user_id,
                'transaction_date': trans_date,
                'revenue': round(revenue, 2),
                'category': category,
                'channel': channel
            })
            
            transaction_id += 1
    
    return pd.DataFrame(transactions)

# ==================== ДОБАВЛЕНИЕ "ГРЯЗИ" ====================
def add_data_issues(df):
    """Добавляет намеренные проблемы в данные для практики очистки"""
    
    print(f"Исходный размер данных: {len(df)} строк")
    
    # 1. Дубликаты transaction_id (50 штук)
    duplicate_indices = np.random.choice(df.index, size=50, replace=False)
    duplicates = df.loc[duplicate_indices].copy()
    df = pd.concat([df, duplicates], ignore_index=True)
    print(f"Добавлено 50 дубликатов transaction_id")
    
    # 2. Пропуски в revenue (100 штук)
    valid_indices = df[df['revenue'].notna()].index
    missing_indices = np.random.choice(valid_indices, size=100, replace=False)
    df.loc[missing_indices, 'revenue'] = np.nan
    print(f"Добавлено 100 пропусков в revenue")
    
    # 3. Отрицательные значения revenue (30 штук)
    valid_indices = df[df['revenue'].notna() & (df['revenue'] > 0)].index
    negative_indices = np.random.choice(valid_indices, size=30, replace=False)
    df.loc[negative_indices, 'revenue'] = -df.loc[negative_indices, 'revenue']
    print(f"Добавлено 30 отрицательных значений revenue")
    
    # 4. Опечатки в category (20 штук)
    typo_map = {
        'Electronics': 'Electonics',
        'Clothing': 'clothng',
        'Home': 'Hme',
        'Food': 'Fodd',
        'Beauty': 'Beuty'
    }
    
    for category, typo in typo_map.items():
        cat_indices = df[df['category'] == category].index
        if len(cat_indices) >= 4:
            typo_indices = np.random.choice(cat_indices, size=4, replace=False)
            df.loc[typo_indices, 'category'] = typo
    print(f"Добавлено 20 опечаток в category")
    
    # 5. Даты в будущем (15 штук - октябрь-ноябрь 2026)
    valid_indices = df[df['transaction_date'] <= END_DATE].index
    future_indices = np.random.choice(valid_indices, size=15, replace=False)
    future_dates = [
        datetime(2026, 10, random.randint(1, 28)),
        datetime(2026, 11, random.randint(1, 28))
    ]
    for idx, future_idx in enumerate(future_indices):
        df.loc[future_idx, 'transaction_date'] = future_dates[idx % 2]
    print(f"Добавлено 15 дат в будущем (октябрь-ноябрь 2026)")
    
    # 6. Пустые user_id (10 штук)
    valid_indices = df[df['user_id'].notna()].index
    empty_user_indices = np.random.choice(valid_indices, size=10, replace=False)
    df.loc[empty_user_indices, 'user_id'] = np.nan
    print(f"Добавлено 10 пустых user_id")
    
    print(f"Итоговый размер данных: {len(df)} строк")
    
    return df

# ==================== ОСНОВНАЯ ФУНКЦИЯ ====================
def main():
    print("=" * 60)
    print("Генерация данных для когортного анализа")
    print("=" * 60)
    
    # Генерируем пользователей
    print("\n1. Генерация пользователей...")
    users_df = generate_users()
    print(f"Создано {len(users_df)} пользователей")
    
    # Генерируем транзакции
    print("\n2. Генерация транзакций...")
    transactions_df = generate_transactions(users_df)
    print(f"Создано {len(transactions_df)} транзакций")
    
    # Добавляем "грязь"
    print("\n3. Добавление проблем в данные...")
    transactions_df = add_data_issues(transactions_df)
    
    # Сохраняем в CSV
    print(f"\n4. Сохранение в {OUTPUT_PATH}...")
    transactions_df.to_csv(OUTPUT_PATH, index=False)
    
    # Статистика
    print("\n" + "=" * 60)
    print("Статистика данных:")
    print("=" * 60)
    print(f"Всего строк: {len(transactions_df)}")
    print(f"Уникальных пользователей: {transactions_df['user_id'].nunique()}")
    print(f"Уникальных транзакций: {transactions_df['transaction_id'].nunique()}")
    print(f"Диапазон дат: {transactions_df['transaction_date'].min()} - {transactions_df['transaction_date'].max()}")
    print(f"Общая выручка: ${transactions_df['revenue'].sum():,.2f}")
    print(f"Средний чек: ${transactions_df['revenue'].mean():,.2f}")
    print("\nРаспределение по каналам:")
    print(transactions_df['channel'].value_counts())
    print("\nРаспределение по категориям:")
    print(transactions_df['category'].value_counts())
    print("\n" + "=" * 60)
    print("Генерация завершена!")
    print("=" * 60)

if __name__ == "__main__":
    main()