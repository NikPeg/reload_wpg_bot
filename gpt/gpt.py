import openai
import json
import os
import time 
import random
current_dir = os.path.dirname(os.path.abspath(__file__))
user_path = os.path.join(current_dir, "..", "user.json")
config_path = os.path.join(current_dir, "..", "config.json")
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


def chat_gpt(thread, text:str, assist_id = "1"):
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
            return  "failed"
        time.sleep(1)
    messages = openai.beta.threads.messages.list(thread_id=thread, order="asc")
    last_assistant_message = next((msg for msg in reversed(messages.data) if msg.role == "assistant"), None)
    if last_assistant_message:
        for content_item in last_assistant_message.content:
            if content_item.type == "text":
                return content_item.text.value




def country_report(thread_id, assist_id, country, text):
    data = {
        "Инферия": 0,
        "Мордор": 0,
        "Рамондана": 0,
        "Хуан-Фернандес": 0,
        "ГСКСР": 0,
        "Лурк": 0,
        "ФТК": 0,
        "Шайервуд": 0,
        "Британия": 0
        }
    final_data = {
        "Инферия": 0,
        "Мордор": 0,
        "Рамондана": 0,
        "Хуан-Фернандес": 0,
        "ГСКСР": 0,
        "Лурк": 0,
        "ФТК": 0,
        "Шайервуд": 0,
        "Британия": 0
        }
    final_data[country] = text
    del data[country]
    random_one = random.choice(list(data.keys()))
    final_data[random_one] = 1
    del data[random_one]
    for key in list(data.keys()):
        if random.random() <= 0.2:
            final_data[key] = 2
            del data[key]
    
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
    messages = openai.beta.threads.messages.list(thread_id=thread_id, order="asc")
    last_assistant_message = next((msg for msg in reversed(messages.data) if msg.role == "assistant"), None)
    if last_assistant_message:
        for content_item in last_assistant_message.content:
            if content_item.type == "text":
                return content_item.text.value

if __name__ == "__main__":
    text = new_assist()
    # text = chat_gpt(thread = "thread_P67niks6tc70bVcHYFX7PWPk", text = f""" "GDP": [750, 800, 860], "population": [9,10,9],"rating_government": [95,90,93]" """, assist_id="asst_kDUKu8X0XuiHG06XyJsXA4nO")
    #text = chat_gpt(thread = "thread_SOJeXKOSD5I3EpeyyfNUA1Xl", text = f"Приказываю напасть на лурк", assist_id="asst_Sw6TCHWpN8TlilWB0O5gZzxE")
    print(text)
    #text = country_report("thread_5aSqLgWWRAok4gqmqW0JXItY", "asst_qTNw4fBtCWneSa0fokdyG57J", "Лурк", "приказываю запретить фтк вести торговую деятельность")
    #print(text)
    #text = chat_gpt(thread = "thread_5aSqLgWWRAok4gqmqW0JXItY", text = f"Сегодня в Лурке был выполнен приказ звучащий как: построить завод свинца. Подведи итоги этого события", assist_id="asst_rn04wllKx0B74u4dM13RvUnj")
    #print(text) 
    
    
    pass   