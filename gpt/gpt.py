import openai
import json
import os
import time 
import random
import threading
from typing import Optional

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


def chat_gpt(thread, text: str, assist_id="1") -> Optional[str]:
    """
    Send a message to the shared thread and wait if there's an active run.
    
    Args:
        thread: The shared OpenAI thread ID
        text: User's message
        assist_id: Assistant ID to use
        
    Returns:
        Assistant's response or None if there was an error or timeout (3 minutes)
    """
    try:
        # Add the user's message to the thread
        openai.beta.threads.messages.create(
            thread_id=thread,
            role="user",
            content=text
        )
        
        # Create a run with the specified assistant
        run = openai.beta.threads.runs.create(
            thread_id=thread,
            assistant_id=assist_id
        )
        
        # Set timeout: 3 minutes = 180 seconds
        timeout = 180
        start_time = time.time()
        
        # Poll until the run completes or times out
        while True:
            # Check if we've exceeded the timeout
            if time.time() - start_time > timeout:
                print("Operation timed out after 3 minutes")
                # Attempt to cancel the run
                try:
                    openai.beta.threads.runs.cancel(
                        thread_id=thread,
                        run_id=run.id
                    )
                except:
                    # If cancellation fails, just continue to return None
                    return None
            
            # Get the current state of the run
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                break
            elif run_status.status == "failed" or run_status.status == "cancelled":
                return None
            
            # Wait before polling again
            time.sleep(1)
        
        # Get the latest messages from the thread (assistant's response)
        messages = openai.beta.threads.messages.list(
            thread_id=thread
        )
        
        # Get the first assistant message (latest response)
        for message in messages.data:
            if message.role == "assistant":
                # Return the content of the message
                return message.content[0].text.value
        
        return None
    except Exception as e:
        print(f"Error in chat_gpt: {e}")
        return None


def country_report(*args, **kwargs):
    return ""


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

