import json
import openai
import telebot
from telebot import types
import datetime
import time

with open("messages.json", "r", encoding='utf-8') as messages:
    txt = json.load(messages)
with open("config.json", "r", encoding='utf-8') as config:
    config_bd = json.load(config)
bot = telebot.TeleBot(config_bd["tg_token"])
openai.api_key = config_bd["chatGPT_token"]


def user_get_thread(message):
    with open("user.json", 'r+', encoding='utf-8') as user:
        data = json.load(user)
    id = str(message.chat.id)
    user_country = data[id]["country"]
    assist_id = config_bd[user_country]
    thread = openai.beta.threads.create()
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assist_id,
    )
    user_data_upgrade(message, "id_thread", str(thread.id))
def user_requests_upgrade(message):
    with open("user.json", 'r+', encoding='utf-8') as f:
        data = json.load(f)
        id = str(message.chat.id)
        now = datetime.datetime.now()
        req = data[id]["sub_lvl"]
        if req == 1:
            req = 1
        elif req == 2:
            req = 5
        elif req == 3:
            req = 100500
        else:
            print("Плохо мне")
        for req_time in data[id]["req"][:]: #копируем массив чтобы не было ошибки
            try:
                datetime.datetime.fromisoformat(req_time)
            except (ValueError, TypeError):
                data[id]["req"] = []
                break
        data[id]["req"] = [
        req_time for req_time in data[id]["req"]
        if (now - datetime.datetime.fromisoformat(req_time)).days < 1
                        ]
        if len(data[id]["req"]) < req:
            data[id]["req"].append(now.isoformat())
            f.seek(0)
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.truncate()
            return "success"
        else:
            bot.send_message(message.chat.id, text=txt["msg"]["max_req"])

            f.seek(0)
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.truncate()
def reg_proof(id:str = "str please "):
    with open("user.json", 'r+', encoding='utf-8') as user:
        data = json.load(user)
        if id in data:
            return "logged" 
        else:
            return "not logged"
def user_data_upgrade(message, key:str = "str please", value:str = "str please"):
    id = str(message.chat.id)
    with open("user.json", 'r+', encoding='utf-8') as user:
        data = json.load(user)
        if id in data:
            if key == "country":
                if data[value] == id:
                    bot.send_message(message.chat.id, txt["msg"]["country_choose2_himself"].format(country=value))
                    return "busy himself"
                elif data[value] != 0:
                    bot.send_message(message.chat.id, txt["msg"]["country_choose2_busy"].format(country=value))
                    return "busy somebody"
                else:
                    for country in txt["btn"]["country"]:
                        if data[country] == id:
                            data[country] = 0
                            data[value] = id
                            data[id][key] = value
                            user.seek(0)
                            json.dump(data, user, indent=4, ensure_ascii=False)
                            user.truncate()
                            bot.send_message(message.chat.id, text = txt["msg"]["country_choose2"].format(country=str(message.text)))
                            return "success"
            if key == "sub_lvl":
                data[id][key] = value
                user.seek(0)
                json.dump(data, user, indent=4, ensure_ascii=False)
                user.truncate()
                bot.send_message(message.chat.id, text = txt["msg"]["sub_done"].format(sub_lvl=data[id][key]))
                return "success"
            if key == "id_thread":
                data[id][key] = value
                user.seek(0)
                json.dump(data, user, indent=4, ensure_ascii=False)
                user.truncate()
                return "successs"
        else:
            data[id] = {
                "nickname":str(message.from_user.username),
                "id_thread":"None",
                key:value,
                "sub_lvl":"0",
                "req":"0"
            }
            user.seek(0)
            json.dump(data, user, indent=4, ensure_ascii=False)
            user.truncate()
            bot.send_message(message.chat.id, text = txt["msg"]["country_choose2"].format(country=str(message.text)))
            return "new user"
def chat_gpt(message):
    with open("user.json", 'r+', encoding='utf-8') as user:
        data = json.load(user)
    user_id = str(message.chat.id)
    if user_id not in data or "country" not in data[user_id] or "id_thread" not in data[user_id]:
        bot.send_message(message.chat.id, text = "Произошла ошибка, пожалуйста, перезапустите бота.")
        return
    user_country = data[user_id]["country"]
    assist_id = config_bd[user_country]
    thread_id = data[user_id]["id_thread"]
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message.text
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
            bot.send_message(message.chat.id, text="Произошла ошибка при выполнении запроса.")
            return
        time.sleep(1)
    messages = openai.beta.threads.messages.list(thread_id=thread_id, order="asc")
    last_assistant_message = next((msg for msg in reversed(messages.data) if msg.role == "assistant"), None)
    if last_assistant_message:
        for content_item in last_assistant_message.content:
            if content_item.type == "text":
                markup = types.ReplyKeyboardMarkup()
                btn1 = types.KeyboardButton(text=txt["btn"]["main_win"][0])
                btn2 = types.KeyboardButton(text=txt["btn"]["main_win"][1])
                btn3 = types.KeyboardButton(text=txt["btn"]["main_win"][2])
                markup.row(btn1, btn2, btn3)
                btn4 = types.KeyboardButton(text=txt["btn"]["main_win"][3])
                btn5 = types.KeyboardButton(text=txt["btn"]["main_win"][4])
                btn6 = types.KeyboardButton(text=txt["btn"]["main_win"][5])
                markup.row(btn4, btn5, btn6)
                bot.send_message(message.chat.id, text=content_item.text.value,reply_markup=markup)


@bot.message_handler(func=lambda message: True)
def main_win(message):
    if reg_proof(str(message.chat.id)) == "logged":
        markup = types.ReplyKeyboardMarkup()
        btn1 = types.KeyboardButton(text=txt["btn"]["main_win"][0])
        btn2 = types.KeyboardButton(text=txt["btn"]["main_win"][1])
        btn3 = types.KeyboardButton(text=txt["btn"]["main_win"][2])
        markup.row(btn1, btn2, btn3)
        btn4 = types.KeyboardButton(text=txt["btn"]["main_win"][3])
        btn5 = types.KeyboardButton(text=txt["btn"]["main_win"][4])
        btn6 = types.KeyboardButton(text=txt["btn"]["main_win"][5])
        markup.row(btn4, btn5, btn6)
        with open("user.json", "r", encoding='utf-8') as user:
            user = json.load(user)
        bot.send_message(message.chat.id, text = txt["msg"]["main_win"].format(name=str(message.from_user.first_name), country=str(user[str(message.chat.id)]["country"])), reply_markup=markup)
        bot.register_next_step_handler(message, main_win1)
    elif reg_proof(str(message.chat.id)) == "not logged": 
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(text=txt["btn"]["start1"], url = txt["btn"]["start1_url"])
        markup.add(btn1)
        bot.send_message(message.chat.id, txt["msg"]["start1"] , reply_markup=markup)
        markup = types.ReplyKeyboardMarkup()
        btn2 = types.KeyboardButton(txt["btn"]["start2"])
        markup.add(btn2)
        bot.send_message(message.chat.id, txt["msg"]["start2"], reply_markup=markup)
        bot.register_next_step_handler(message, country_choose)


def main_win1(message):
    if str(message.text) in txt["btn"]["main_win"]:
        if message.text == str(txt["btn"]["main_win"][0]):
            bot.send_message(message.chat.id, text = "Да не сделал я еще")
            bot.register_next_step_handler(message, main_win1)
        if message.text == str(txt["btn"]["main_win"][1]):
            with open("map.png", 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
            with open("map1.png", 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
            bot.register_next_step_handler(message, main_win1)
        if message.text == str(txt["btn"]["main_win"][2]):
            bot.send_message(message.chat.id, text = "Да не сделал я еще")
            bot.register_next_step_handler(message, main_win1)
        if message.text == str(txt["btn"]["main_win"][3]):
            bot.send_message(message.chat.id, text = "Да не сделал я еще")
            bot.register_next_step_handler(message, main_win1)
        if message.text == str(txt["btn"]["main_win"][4]):
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton(text=txt["btn"]["country"][0])
            btn2 = types.KeyboardButton(text=txt["btn"]["country"][1])
            btn3 = types.KeyboardButton(text=txt["btn"]["country"][2])
            markup.row(btn1, btn2, btn3)
            btn4 = types.KeyboardButton(text=txt["btn"]["country"][3])
            btn5 = types.KeyboardButton(text=txt["btn"]["country"][4])
            btn6 = types.KeyboardButton(text=txt["btn"]["country"][5])
            markup.row(btn4, btn5, btn6)
            btn7 = types.KeyboardButton(text=txt["btn"]["country"][6])
            btn8 = types.KeyboardButton(text=txt["btn"]["country"][7])
            btn9 = types.KeyboardButton(text=txt["btn"]["country"][8])
            markup.row(btn7, btn8, btn9)
            bot.send_message(message.chat.id, text = txt["msg"]["country_choose"], reply_markup=markup)
            bot.register_next_step_handler(message, country_choose2)
        
        if message.text == str(txt["btn"]["main_win"][5]):
            with open("sub.png", 'rb') as photo:
                markup = types.ReplyKeyboardMarkup()
                btn1 = types.KeyboardButton(txt["btn"]["sub"][0])
                btn2 = types.KeyboardButton(txt["btn"]["sub"][1])
                btn3 = types.KeyboardButton(txt["btn"]["sub"][2])
                markup.add(btn1, btn2, btn3)
                bot.send_photo(message.chat.id, photo, reply_markup=markup)
            bot.register_next_step_handler(message, sub)
    else:
        #нейро
        if user_requests_upgrade(message) == "success":
            chat_gpt(message)
        bot.register_next_step_handler(message, main_win1)



def country_choose(message):
    
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton(text=txt["btn"]["country"][0])
    btn2 = types.KeyboardButton(text=txt["btn"]["country"][1])
    btn3 = types.KeyboardButton(text=txt["btn"]["country"][2])
    markup.row(btn1, btn2, btn3)
    btn4 = types.KeyboardButton(text=txt["btn"]["country"][3])
    btn5 = types.KeyboardButton(text=txt["btn"]["country"][4])
    btn6 = types.KeyboardButton(text=txt["btn"]["country"][5])
    markup.row(btn4, btn5, btn6)
    btn7 = types.KeyboardButton(text=txt["btn"]["country"][6])
    btn8 = types.KeyboardButton(text=txt["btn"]["country"][7])
    btn9 = types.KeyboardButton(text=txt["btn"]["country"][8])
    markup.row(btn7, btn8, btn9)
    bot.send_message(message.chat.id, text = txt["msg"]["country_choose"], reply_markup=markup)
    bot.register_next_step_handler(message, country_choose2)

def country_choose2(message):
    if str(message.text) in txt["btn"]["country"]:
        refund = user_data_upgrade(message, "country", str(message.text))
        if refund == "success":
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton(text=txt["btn"]["main_win"][0])
            btn2 = types.KeyboardButton(text=txt["btn"]["main_win"][1])
            btn3 = types.KeyboardButton(text=txt["btn"]["main_win"][2])
            markup.row(btn1, btn2, btn3)
            btn4 = types.KeyboardButton(text=txt["btn"]["main_win"][3])
            btn5 = types.KeyboardButton(text=txt["btn"]["main_win"][4])
            btn6 = types.KeyboardButton(text=txt["btn"]["main_win"][5])
            markup.row(btn4, btn5, btn6)
            user_get_thread(message)
            with open("user.json", "r", encoding='utf-8') as user:
                user = json.load(user)
                bot.send_message(message.chat.id, text = txt["msg"]["main_win"].format(name=str(message.from_user.first_name), country=str(user[str(message.chat.id)]["country"])), reply_markup=markup)
            bot.register_next_step_handler(message, main_win1)
            
        elif refund == "new user":
            user_get_thread(message)
            with open("sub.png", 'rb') as photo:
                markup = types.ReplyKeyboardMarkup()
                btn1 = types.KeyboardButton(txt["btn"]["sub"][0])
                btn2 = types.KeyboardButton(txt["btn"]["sub"][1])
                btn3 = types.KeyboardButton(txt["btn"]["sub"][2])
                markup.add(btn1, btn2, btn3)
                bot.send_photo(message.chat.id, photo, reply_markup=markup)
            bot.register_next_step_handler(message, sub)
    else:
        bot.send_message(message.chat.id, text = txt["msg"]["country_choose2_er"])
        bot.register_next_step_handler(message, country_choose)


def sub(message):
    if str(message.text) in txt["btn"]["sub"]:
        if str(message.text) == txt["btn"]["sub"][0]:
            user_data_upgrade(message, "sub_lvl", 1)
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton(text=txt["btn"]["main_win"][0])
            btn2 = types.KeyboardButton(text=txt["btn"]["main_win"][1])
            btn3 = types.KeyboardButton(text=txt["btn"]["main_win"][2])
            markup.row(btn1, btn2, btn3)
            btn4 = types.KeyboardButton(text=txt["btn"]["main_win"][3])
            btn5 = types.KeyboardButton(text=txt["btn"]["main_win"][4])
            btn6 = types.KeyboardButton(text=txt["btn"]["main_win"][5])
            markup.row(btn4, btn5, btn6)
            with open("user.json", "r", encoding='utf-8') as user:
                user = json.load(user)
            bot.send_message(message.chat.id, text = txt["msg"]["main_win"].format(name=str(message.from_user.first_name), country=str(user[str(message.chat.id)]["country"])), reply_markup=markup)
            bot.register_next_step_handler(message, main_win1)
        if str(message.text) == txt["btn"]["sub"][1]:
            user_data_upgrade(message, "sub_lvl", 2)
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton(text=txt["btn"]["main_win"][0])
            btn2 = types.KeyboardButton(text=txt["btn"]["main_win"][1])
            btn3 = types.KeyboardButton(text=txt["btn"]["main_win"][2])
            markup.row(btn1, btn2, btn3)
            btn4 = types.KeyboardButton(text=txt["btn"]["main_win"][3])
            btn5 = types.KeyboardButton(text=txt["btn"]["main_win"][4])
            btn6 = types.KeyboardButton(text=txt["btn"]["main_win"][5])
            markup.row(btn4, btn5, btn6)
            with open("user.json", "r", encoding='utf-8') as user:
                user = json.load(user)
            bot.send_message(message.chat.id, text = txt["msg"]["main_win"].format(name=str(message.from_user.first_name), country=str(user[str(message.chat.id)]["country"])), reply_markup=markup)
            bot.register_next_step_handler(message, main_win1)
        if str(message.text) == txt["btn"]["sub"][2]:
            user_data_upgrade(message, "sub_lvl", 3)
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton(text=txt["btn"]["main_win"][0])
            btn2 = types.KeyboardButton(text=txt["btn"]["main_win"][1])
            btn3 = types.KeyboardButton(text=txt["btn"]["main_win"][2])
            markup.row(btn1, btn2, btn3)
            btn4 = types.KeyboardButton(text=txt["btn"]["main_win"][3])
            btn5 = types.KeyboardButton(text=txt["btn"]["main_win"][4])
            btn6 = types.KeyboardButton(text=txt["btn"]["main_win"][5])
            markup.row(btn4, btn5, btn6)
            with open("user.json", "r", encoding='utf-8') as user:
                user = json.load(user)
            bot.send_message(message.chat.id, text = txt["msg"]["main_win"].format(name=str(message.from_user.first_name), country=str(user[str(message.chat.id)]["country"])), reply_markup=markup)
            bot.register_next_step_handler(message, main_win1)
    else:
        bot.send_message(message.chat.id, text = txt["msg"]["sub_err"])
        print("meow")
        bot.register_next_step_handler(message, main_win1)

def send_mail(message):
    if str(message.text) in txt["btn"]["country"]:
        id = 
        bot.send_message(message)

bot.polling(none_stop=True)