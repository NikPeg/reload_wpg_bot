import openai
import time

# Замените на ваш API-ключ
openai.api_key = "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"

# Замените на ID вашего существующего ассистента
ASSISTANT_ID = "asst_ufiBUoTqoFYu3Yrrxeu9M7HI"

# --- Создание треда ---
thread = openai.beta.threads.create()
thread_id = thread.id
print(f"Тред с ID {thread_id} создан.")

# --- Цикл отправки сообщений ---
while True:
    message_text = input("Введите сообщение (или 'exit' для выхода): ")
    if message_text.lower() == "exit":
        break

    # --- Отправка сообщения ---
    message = openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_text
    )
    print(f"Сообщение с ID {message.id} отправлено в тред.")

    # --- Запуск треда ---
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID
    )
    print(f"Тред с ID {thread_id} запущен с ID {run.id}.")

    # --- Ожидание и получение ответа ---
    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id).status
        print(f"Статус запроса: {run_status}")

        if run_status == "completed":
            messages = openai.beta.threads.messages.list(thread_id=thread_id)
            for message in messages:
                if message.role == "assistant":
                    print(f"Ответ от ассистента: {message.content}")
            break
        elif run_status == "failed":
            print("Произошла ошибка при выполнении запроса.")
            break
        time.sleep(1)

print("Программа завершена.")