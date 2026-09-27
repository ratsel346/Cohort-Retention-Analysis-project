-- SQL-скрипт для демо-проекта
-- Используется MySQL


WITH users_all_cohorta AS (
	SELECT user_id,
		MIN(DATE_FORMAT(transaction_date, '%Y-%m')) AS month_cohorta, 
        MIN(transaction_date) AS first_cohorta_date
	FROM ecommerce
    GROUP BY user_id
),
cohorta_activity AS (
	SELECT uac.month_cohorta,
		PERIOD_DIFF(
        DATE_FORMAT(t.transaction_date, '%Y%m'),
        DATE_FORMAT(uac.first_cohorta_date, '%Y%m')
        ) AS cohort_index,
        COUNT(distinct t.user_id) AS active_users
	FROM ecommerce t
    JOIN users_all_cohorta uac ON t.user_id = uac.user_id 
    GROUP BY uac.month_cohorta,
		PERIOD_DIFF(
			DATE_FORMAT(t.transaction_date, '%Y%m'),
			DATE_FORMAT(uac.first_cohorta_date, '%Y%m')
			)
),
cohorta_sizes AS (
	SELECT month_cohorta,
		COUNT(DISTINCT user_id) AS cohorta_size
	FROM users_all_cohorta
    GROUP BY month_cohorta
)
SELECT 
	ca.month_cohorta,
    ca.cohort_index,
    cs.cohorta_size,
    ca.active_users,
    ROUND((ca.active_users/cs.cohorta_size * 100.0), 2) AS retention_rate
FROM cohorta_activity ca
JOIN cohorta_sizes cs ON ca.month_cohorta = cs.month_cohorta
ORDER BY ca.month_cohorta ASC, ca.cohort_index ASC
