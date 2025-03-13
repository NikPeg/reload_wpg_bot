import openai
import json
import os
import time 
import random
current_dir = os.path.dirname(os.path.abspath(__file__))
user_path = os.path.join(current_dir, "..", "user.json")
config_path = os.path.join(current_dir, "..", "config.json")
country_path = os.path.join(current_dir, "..", "country.json")
with open(config_path, 'r+', encoding='utf-8') as cfile:
        config_bd = json.load(cfile)
openai.api_key = config_bd["chatGPT_token"]



def user_get_thread():
    thread = openai.beta.threads.create()
    return thread.id

def new_assist():
    assistant = openai.beta.assistants.create(
    name="RELOAD_GRAF",
    instructions="""Запрос:

Оцени влияние на параметры ниже, событий, которые произошли за ЭТОТ год в контексте выше (контекст заканчивается фразой от игрока: {country} встретил(а) новый {year} год следующей новостью)

Входные данные:

{
    "GDP": [250, 260, 255],
    "population": [12, 16, 18],
    "rating_government": [27, 29, 240]
}


Вывод только такой:

{
    "GDP": значение (int),
    "population": значение (int),
    "rating_government": значение (int)
}


Важные моменты:

Обязательно включайте входные данные (JSON).
Ответ должен быть только в формате JSON. Никаких дополнительных пояснений, комментариев или текста вне JSON.
Если треда нет, значения в JSON должны быть случайными, но реалистичными. (Например, не стоит делать рейтинг правительства отрицательным или население резко уменьшать/увеличивать в разы).
Интерполируйте значения на СЛЕДУЮЩИЙ год. То есть, вы должны предсказать, как изменятся параметры после событий текущего года.
Изменения в значениях не должны быть больше 50%.
Ключи должны оставаться теми же: “GDP”, “population”, “rating_government”.
Значения должны быть целыми числами.
    """,
    model="gpt-4-1106-preview"
)
    return assistant


def chat_gpt(thread, text: str, assist_id="1"):
    assist_id = assist_id
    openai.beta.threads.messages.create(
        thread_id=thread,
        role="user",
        content=text
    )
    try:
        run = openai.beta.threads.runs.create(
            thread_id=thread,
            assistant_id=assist_id
        )
    except:
        try:
            time.sleep(3)
            run = openai.beta.threads.runs.create(
                thread_id=thread,
                assistant_id=assist_id
            )
        except:
            return None
    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread, run_id=run.id).status
        if run_status == "completed":
            break
        elif run_status == "failed":
            return "failed"
        time.sleep(1)
    try:
        messages = openai.beta.threads.messages.list(thread_id=thread, order="desc", limit=1)
        if messages.data:
            last_message = messages.data[0] # Самое последнее сообщение
            if last_message.role == "assistant": # проверяем роль
                if last_message.content:
                    for content_item in last_message.content:
                        if content_item.type == "text":
                            return content_item.text.value
    except Exception as e: # Обрабатываем ошибки
        print(f"Ошибка при получении сообщения: {e}")
        return None




def country_report(thread_id, assist_id, country, text, bot=None):
    data = {}
    with open(country_path, 'r+', encoding='utf-8') as cfile:
        country_bd = json.load(cfile)
        for country_1 in country_bd:
            data[country_1] = 0
    final_data = dict(data)
    
    final_data[country] = text
    del data[country]
    random_one = random.choice(list(data.keys()))
    final_data[random_one] = 1
    del data[random_one]
    for key in list(data.keys()):
        if random.random() <= 0.15:
            final_data[key] = 2
            data.pop(key, None)
        elif key[:-1] in text:
            final_data[key] = 2
            data.pop(key, None)
    final_data = str({key: value for key, value in final_data.items() if value != 0})
    print(final_data)
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=final_data
    )
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assist_id
    )
    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id).status
        if run_status == "completed":
            break
        elif run_status == "failed":
            return  "failed"
        time.sleep(1)
    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    latest_message = messages.data[0]
    latest_message_text = latest_message.content[0].text.value
    return latest_message_text

def ask(text):
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    # Use your specific run and thread IDs
    # thread_HS5tY59a2ixWRQuvQma9RjBL while a run run_zCwyNIbj6AkozigvNlk6qxnS is active
    run_id = "run_zCwyNIbj6AkozigvNlk6qxnS"
    thread_id = "thread_HS5tY59a2ixWRQuvQma9RjBL"

    # Cancel the run
    response = openai.beta.threads.runs.cancel(
        thread_id=thread_id,
        run_id=run_id
    )
    # Check run status
    run = openai.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id
    )

    print(f"Run status: {run.status}")

