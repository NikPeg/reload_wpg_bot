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
    
    # First, check if there are any active runs on the thread
    try:
        runs = openai.beta.threads.runs.list(thread_id=thread)
        active_runs = [run for run in runs.data if run.status in ["queued", "in_progress", "cancelling"]]
        
        # If there are active runs, wait for them to complete
        for run in active_runs:
            wait_for_run_completion(thread, run.id)
    except Exception as e:
        print(f"Error checking active runs: {str(e)}")
    
    # Now it's safe to add a new message
    try:
        message = openai.beta.threads.messages.create(
            thread_id=thread,
            role="user",
            content=text
        )
    except Exception as e:
        print(f"Error creating message: {str(e)}")
        time.sleep(1)
        message = openai.beta.threads.messages.create(
            thread_id=thread,
            role="user",
            content=text
        )
    
    # Create a new run
    try:
        run = openai.beta.threads.runs.create(
            thread_id=thread,
            assistant_id=assist_id
        )
    except Exception as e:
        print(f"Error creating run: {str(e)}")
        try:
            time.sleep(3)
            run = openai.beta.threads.runs.create(
                thread_id=thread,
                assistant_id=assist_id
            )
        except Exception as e:
            print(f"Failed to create run after retry: {str(e)}")
            return None
    
    # Wait for the run to complete and return the result
    result = wait_for_run_completion(thread, run.id)
    return result


def wait_for_run_completion(thread_id, run_id, timeout=30):
    """Wait for a run to complete and return the result."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            run = openai.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status == "completed":
                # Retrieve the latest messages
                messages = openai.beta.threads.messages.list(
                    thread_id=thread_id
                )
                # Return the assistant's most recent message
                for msg in messages.data:
                    if msg.role == "assistant":
                        # Extract text content from the message
                        content = [part.text.value for part in msg.content if hasattr(part, 'text')]
                        return '\n'.join(content) if content else None
                return None
            
            elif run.status in ["failed", "cancelled", "expired"]:
                print(f"Run ended with status: {run.status}")
                return None
            
            # Sleep before checking again
            time.sleep(2)
            
        except Exception as e:
            print(f"Error checking run status: {str(e)}")
            time.sleep(2)
    
    print("Run timed out")
    return None



def country_report(thread_id, assist_id, country, text, answer, bot=None):
    data = {}
    with open(country_path, 'r+', encoding='utf-8') as cfile:
        country_bd = json.load(cfile)
        for country_1 in country_bd:
            data[country_1] = 0
    final_data = dict(data)
    
    final_data[country] = text
    del data[country]
    for key in list(data.keys()):
        if key[:-1] in text or key[:-1] in answer:
            final_data[key] = 2
            data.pop(key, None)
    final_data = str({key: value for key, value in final_data.items() if value != 0})
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
    if not latest_message.content:
        return "Нет ответа"
    latest_message_text = latest_message.content[0].text.value
    return latest_message_text.replace("**", "")

def ask(text):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
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

