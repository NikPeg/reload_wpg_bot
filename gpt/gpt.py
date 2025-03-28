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


# Global lock for the single shared thread
_thread_lock = threading.Lock()
_active_run = None


def chat_gpt(thread, text: str, assist_id="1"):
    """
    Send a message to the shared thread and wait if there's an active run.
    
    Args:
        thread: The shared OpenAI thread ID
        text: User's message
        assist_id: Assistant ID to use
        
    Returns:
        Assistant's response or None if there was an error
    """
    global _active_run
    
    # Acquire the global lock to ensure exclusive access to the thread
    with _thread_lock:
        # Check if there's an active run and wait for it to complete
        if _active_run:
            wait_for_run(thread, _active_run)
            _active_run = None
        
        # Send the message
        try:
            openai.beta.threads.messages.create(
                thread_id=thread,
                role="user",
                content=text
            )
        except Exception as e:
            print(f"Error sending message, retrying: {str(e)}")
            time.sleep(1)
            try:
                openai.beta.threads.messages.create(
                    thread_id=thread,
                    role="user",
                    content=text
                )
            except Exception as e:
                print(f"Failed to send message after retry: {str(e)}")
                return None
        
        # Create a new run
        try:
            run = openai.beta.threads.runs.create(
                thread_id=thread,
                assistant_id=assist_id
            )
            # Store the active run ID
            _active_run = run.id
        except Exception as e:
            print(f"Error creating run, retrying: {str(e)}")
            time.sleep(3)
            try:
                run = openai.beta.threads.runs.create(
                    thread_id=thread,
                    assistant_id=assist_id
                )
                _active_run = run.id
            except Exception as e:
                print(f"Failed to create run after retry: {str(e)}")
                _active_run = None
                return None
    
    # Wait for the run to complete (released the lock so others can check)
    response = wait_for_run_and_get_response(thread, _active_run)
    
    # Reset the active run when done
    with _thread_lock:
        if _active_run == run.id:
            _active_run = None
            
    return response


def wait_for_run(thread_id: str, run_id: str, timeout: int = 180) -> bool:
    """Wait for a specific run to complete."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            run = openai.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status not in ["queued", "in_progress", "cancelling"]:
                return True  # Run is no longer active
                
            # Sleep before checking again
            time.sleep(1)
            
        except Exception as e:
            print(f"Error checking run status: {str(e)}")
            time.sleep(2)
    
    print(f"Timed out waiting for run {run_id}")
    return False


def wait_for_run_and_get_response(thread_id: str, run_id: str, timeout: int = 180) -> Optional[str]:
    """Wait for a run to complete and return the assistant's response."""
    if wait_for_run(thread_id, run_id, timeout):
        try:
            # Get the assistant's response
            messages = openai.beta.threads.messages.list(thread_id=thread_id)
            for msg in messages.data:
                if msg.role == "assistant":
                    # Extract text content from the message
                    content = [part.text.value for part in msg.content if hasattr(part, 'text')]
                    return '\n'.join(content) if content else None
                    
            return None  # No assistant messages found
            
        except Exception as e:
            print(f"Error retrieving messages: {str(e)}")
            return None
    
    return None  # Run didn't complete successfully


def wait_for_run_completion(thread_id, run_id, timeout=180):
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
                        if not content:
                            print("no content!")
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

