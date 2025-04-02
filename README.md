# reload_bot

1. Запускаем прокси/впн с поддержкой чатгпт
2. Запускаем main.py
3. Готово

Формат конфига:
```
{
    "new_year":"17:27",
    "debug":1,
    "tg_token":"токен_бота",
    "PAYMENTS_ID":"pk_id_cloudpayments",
    "PAYMENTS_TOKEN":"токен_cloudpayments",
    "sub_lvl2_price":150,
    "sub_lvl3_price":450,
    "sub_lvl_req_max_1":1,
    "sub_lvl_req_max_2":5,
    "sub_lvl_req_max_3":100500,
    "chatGPT_token":"sk-токен-гпт",

    "user_event_handler":"asst_общий_ассистент",
    "country_report":"asst_влияния_на_страны",
    "project_assistent":"asst_проекта",
    "statistic_graph":"asst_анализа_показателей",
    "action": "asst_действия",
    "era": "стимпанк",

    "admin_list":[
        "id_админов",
    ]
}
```

Формат country.json:
```
{
    "Инферия": {
        "id": "id пользователя",
        "GDP": [],
        "population": [],
        "rating_government": []
    }
}
```

Формат user.json:
```
{
    "id пользователя": {
        "country": "Хуан-Фернандес",
        "sub_lvl": "1",
        "sub_id": "sc_подписка",
        "id_thread": "thread_id_треда",
        "req": []
    }
}
```
