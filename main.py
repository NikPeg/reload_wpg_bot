import json
import openai
import telebot
from telebot import types
import datetime
import time
import schedule
import datetime
import threading
import cloudpayments
import requests
import uuid
import base64

with open("messages.json", "r", encoding='utf-8') as messages:
    txt = json.load(messages)
with open("config.json", "r", encoding='utf-8') as config:
    config_bd = json.load(config)
bot = telebot.TeleBot(config_bd["tg_token"])
openai.api_key = config_bd["chatGPT_token"]
PUBLIC_ID = config_bd["PAYMENTS_ID"]
API_SECRET =  config_bd["PAYMENTS_TOKEN"]

class MockMessage:
    def __init__(self, chat_id, text):
        self.chat = MockChat(chat_id)
        self.text = text
    def __repr__(self):
        return f"MockMessage(chat_id={self.chat.id}, text='{self.text}')"


class MockChat:
    def __init__(self, chat_id):
        self.id = chat_id
    def __repr__(self):
        return f"MockChat(id={self.id})"

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

def check_subscription_status(subscription_id):
    api = cloudpayments.CloudPayments(PUBLIC_ID, API_SECRET)
    url = "https://api.cloudpayments.ru/subscriptions/get"

    auth_str = f"{PUBLIC_ID}:{API_SECRET}"
    encoded_auth_str = base64.b64encode(auth_str.encode()).decode()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {encoded_auth_str}'
    }
    data = {
        'Id' : subscription_id,
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        response_data = response.json()
        if response_data.get('Success') and response_data['Model']['Status'] == 'Active':
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False

def deactivate_order(order_id):

    api = cloudpayments.CloudPayments(PUBLIC_ID, API_SECRET)
    url = "https://api.cloudpayments.ru/orders/cancel"

    auth_str = f"{PUBLIC_ID}:{API_SECRET}"
    encoded_auth_str = base64.b64encode(auth_str.encode()).decode()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {encoded_auth_str}'
    }
    data = {
        'Id': order_id,
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        response_data = response.json()

        if response_data.get('Success'):
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False


def sub_pay(amount, id, description="Оплата подписки", order_id=None, account_id=None):
    if not order_id:
        order_id = str(uuid.uuid4())
    if not account_id:
        account_id = str(uuid.uuid4())
    api = cloudpayments.CloudPayments(PUBLIC_ID, API_SECRET)
    url = "https://api.cloudpayments.ru/orders/create"
    auth_str = f"{PUBLIC_ID}:{API_SECRET}"
    encoded_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {encoded_auth_str}'
    }
    data = {
        'Amount': amount,
        'Currency': "RUB",
        'Description': description,
        'SubscriptionBehavior':'CreateMonthly',
        'InvoiceId': order_id,
        'AccountId': account_id
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        response_data = response.json()

        if response_data.get('Success'):
            user_data_upgrade(id, "sub_id", response_data['Model']["Id"])
            return response_data['Model']['Url']
        else:
            return "something dont work"
    except requests.exceptions.RequestException:
        return "something dont work"

def check_pay(id):
    api = cloudpayments.CloudPayments(PUBLIC_ID, API_SECRET)
    url = f"https://api.cloudpayments.ru/payments/get"
    auth_str = f"{PUBLIC_ID}:{API_SECRET}"
    encoded_auth_str = base64.b64encode(auth_str.encode()).decode()
    with open("user.json", "r", encoding='utf-8') as user:
        user = json.load(user)
    transaction_id = user[id]["sub_id"]
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {encoded_auth_str}'
    }
    data = {
        'TransactionId': transaction_id,
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        response_data = response.json()
        if response_data.get('Success') and response_data['Model']['Status'] == "Active":
            if response_data['Model']['Amount'] == config_bd["sub_lvl2_price"]:
                user_data_upgrade(id, "sub_lvl", 1)
            if response_data['Model']['Amount'] == config_bd["sub_lvl3_price"]:
                user_data_upgrade(id, "sub_lvl", 2)
            return True
        else:
            
            return False
    except requests.exceptions.RequestException as e:
        print("Произошла ошибка при отправке запроса:", e)
        return False
    
def bot_trac(who, message):
    if who == 1:
        bot.forward_message( 
            chat_id=-4707616830,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )    
    else:
        bot.forward_message(
            chat_id=-4707616830,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
def user_requests_upgrade(message):
    with open("user.json", 'r+', encoding='utf-8') as f:
        data = json.load(f)
        id = str(message.chat.id)
        now = datetime.datetime.now()
        req = data[id]["sub_lvl"]
        if int(req) == 1:
            req = 1
        elif int(req) == 2:
            req = 5
        elif int(req) == 3:
            req = 100500
        else:
            print("Плохо мне")
        for req_time in data[id]["req"][:]: 
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
                    return "busy himself"
                elif data[value] != 0:
                    return "busy somebody"
                for country in txt["btn"]["country"]:
                    if data[country] == id:
                        data[country] = 0
                        data[value] = id
                        data[id]["country"] = value
                        user.seek(0)
                        json.dump(data, user, indent=4, ensure_ascii=False)
                        user.truncate()
                        return "success"
                    
            if key == "sub_lvl":
                data[id][key] = value
                user.seek(0)
                json.dump(data, user, indent=4, ensure_ascii=False)
                user.truncate()
                return "success"
            if key == "id_thread":
                data[id][key] = value
                user.seek(0)
                json.dump(data, user, indent=4, ensure_ascii=False)
                user.truncate()
                return "successs"
            if key == "sub_id":
                data[id]["sub_id"] = value
                user.seek(0)
                json.dump(data, user, indent=4, ensure_ascii=False)
                user.truncate()
                return "successs"
        else:
            if data[value] != 0:
                bot.send_message(message.chat.id, txt["msg"]["country_choose2_busy"].format(country=value))
                return "busy somebody"
            data[id] = {
                "nickname":str(message.from_user.username),
                "id_thread":"None",
                key:value,
                "sub_lvl":"0",
                "sub_id":"0",
                "req":[]
            }
            data[value] = id
            user.seek(0)
            json.dump(data, user, indent=4, ensure_ascii=False)
            user.truncate()
            bot.send_message(message.chat.id, text = txt["msg"]["country_choose2"].format(country=str(message.text)))
            return "new user"

def chat_gpt(message):
    with open("user.json", 'r+', encoding='utf-8') as user:
        data = json.load(user)
    user_id = str(message.chat.id)
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
                bot_trac(1, bot.send_message(message.chat.id, text=content_item.text.value,reply_markup=markup))
                
@bot.message_handler(commands=['answer'])
def handle_answer(message):
    with open("user.json", "r", encoding='utf-8') as user:
        user = json.load(user)
    if str(message.chat.id) in user["admin_list"]:
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
        bot.send_message(message.chat.id, text = txt["msg"]["admin_mail"], reply_markup=markup)
        bot.register_next_step_handler(message, send_admin_mail)



@bot.message_handler(commands=['unsub'])
def unsub(message):
    with open("user.json", "r", encoding='utf-8') as user:
        user = json.load(user)
    if str(message.chat.id) in user["admin_list"]:
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
        bot.send_message(message.chat.id, text = txt["msg"]["admin_unsub"], reply_markup=markup)
        bot.register_next_step_handler(message, unsub2)
def unsub2(message):
    with open("user.json", "r+", encoding='utf-8') as user:
        data = json.load(user)
        country = data[message.text]
        if data[country] != 0:
            del data[country]
            data[message.text] = 0
            user.seek(0)
            json.dump(data, user, indent=4, ensure_ascii=False)
            user.truncate()
    bot.send_message(message.chat.id, text = txt["msg"]["admin_unsub_done"])
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text=txt["btn"]["start1"], url = txt["btn"]["start1_url"])
    markup.add(btn1)
    bot.send_message(message.chat.id, txt["msg"]["start1"] , reply_markup=markup)
    markup = types.ReplyKeyboardMarkup()
    btn2 = types.KeyboardButton(txt["btn"]["start2"])
    markup.add(btn2)
    bot.send_message(message.chat.id, txt["msg"]["start2"], reply_markup=markup)
    bot.register_next_step_handler(message, country_choose)

def send_admin_mail(message):
    if str(message.text) in txt["btn"]["country"]:
        with open("user.json", 'r+', encoding='utf-8') as user:
            data = json.load(user)
        bot.send_message(message.chat.id, text = txt["msg"]["mail_text"])
        bot.register_next_step_handler(message, send_admin_mail1, id=data[str(message.text)])
    else:
        bot.send_message(message.chat.id, text = txt["msg"]["country_choose2_er"])
        bot.register_next_step_handler(message, send_admin_mail)
def send_admin_mail1(message, id):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton(text=txt["btn"]["main_win"][0])
    btn2 = types.KeyboardButton(text=txt["btn"]["main_win"][1])
    btn3 = types.KeyboardButton(text=txt["btn"]["main_win"][2])
    markup.row(btn1, btn2, btn3)
    btn4 = types.KeyboardButton(text=txt["btn"]["main_win"][3])
    btn5 = types.KeyboardButton(text=txt["btn"]["main_win"][4])
    btn6 = types.KeyboardButton(text=txt["btn"]["main_win"][5])
    markup.row(btn4, btn5, btn6)
    bot.send_message(message.chat.id, text = txt["msg"]["mail_done"], reply_markup=markup)
    try:
        with open("user.json", "r", encoding='utf-8') as user:
            user = json.load(user)
        bot.send_message(id, text = txt["msg"]["admin_mail_to"].format(text = message.text)) 
    except ValueError:
        pass
    bot.register_next_step_handler(message, main_win1)


@bot.message_handler(func=lambda message: str(message.chat.id) != "-4707616830")
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
    bot_trac(0, message)
    if str(message.text) in txt["btn"]["main_win"]:
        if message.text == str(txt["btn"]["main_win"][0]):
            with open("user.json", "r", encoding='utf-8') as user:
                user = json.load(user)
            if user[str(message.chat.id)]["sub_lvl"] == 1:
                bot.send_message(str(message.chat.id), text = txt["msg"]["mail_err"])
                bot.register_next_step_handler(message, main_win1)
            else:
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
                bot.send_message(message.chat.id, text = txt["msg"]["mail"], reply_markup=markup)
                bot.register_next_step_handler(message, send_mail)
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
    elif str(message.text) in txt["btn"]["admin_commands"]:
        if message.text in ["answer","/answer"]:
            with open("user.json", "r", encoding='utf-8') as user:
                user = json.load(user)
            if str(message.chat.id) in user["admin_list"]:
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
                bot.send_message(message.chat.id, text = txt["msg"]["admin_mail"], reply_markup=markup)
                bot.register_next_step_handler(message, send_admin_mail)
        if message.text in ["unsub","/unsub"]:
            with open("user.json", "r", encoding='utf-8') as user:
                user = json.load(user)
            if str(message.chat.id) in user["admin_list"]:
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
                bot.send_message(message.chat.id, text = txt["msg"]["admin_unsub"], reply_markup=markup)
                bot.register_next_step_handler(message, unsub2)
    else:
        #нейро
        bot_trac(0, message)
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
        if refund == "busy himself":
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
            bot.send_message(message.chat.id, txt["msg"]["country_choose2_himself"].format(country=str(user[str(message.chat.id)]["country"])), reply_markup=markup)
            bot.register_next_step_handler(message, main_win1)
        if refund == "success":
            user_get_thread(message)
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
            bot.send_message(message.chat.id, text = txt["msg"]["country_choose2"].format(name=str(message.from_user.first_name), country=str(user[str(message.chat.id)]["country"])), reply_markup=markup)
            bot.register_next_step_handler(message, main_win1)
        elif refund == "busy somebody":
            bot.send_message(message.chat.id, txt["msg"]["country_choose2_busy"].format(country=str(user[str(message.chat.id)]["country"])), reply_markup=markup)
            bot.register_next_step_handler(message, country_choose2)
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
            user_data_upgrade(message, "sub_lvl", "1")
            bot.send_message(message.chat.id, text = txt["msg"]["main_win"].format(name=str(message.from_user.first_name), country=str(user[str(message.chat.id)]["country"])), reply_markup=markup)
            bot.register_next_step_handler(message, main_win1)
        if str(message.text) == txt["btn"]["sub"][1]:
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton(text=txt["btn"]["sub_success"])
            btn2 = types.KeyboardButton(text=txt["btn"]["sub_not_success"])
            markup.row(btn1, btn2)
            bot.send_message(message.chat.id, text = txt["msg"]["sub"].format(url = sub_pay(config_bd["sub_lvl2_price"],message)), reply_markup=markup)
            bot.register_next_step_handler(message, sub1, sub_lvl = "2")
        if str(message.text) == txt["btn"]["sub"][2]:
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton(text=txt["btn"]["sub_success"])
            btn2 = types.KeyboardButton(text=txt["btn"]["sub_not_success"])
            markup.row(btn1, btn2)
            bot_trac(1, bot.send_message(message.chat.id, text = txt["msg"]["sub"].format(url = sub_pay(config_bd["sub_lvl3_price"],message)), reply_markup=markup))
            
            bot.register_next_step_handler(message, sub1, sub_lvl = "3")
    else:
        bot.send_message(message.chat.id, text = txt["msg"]["sub_err"])
        bot.register_next_step_handler(message, main_win1)

def sub1(message, sub_lvl):
    #condition = check_pay(str(message.chat.id))
    bot_trac(0, message)
    condition = "meow"
    if message.text == "Оплачена":
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
        user_data_upgrade(message, "sub_lvl", sub_lvl)
        bot.send_message(message.chat.id, text = txt["msg"]["sub_check_found"].format(sub_lvl=sub_lvl), reply_markup=markup)
        bot.register_next_step_handler(message, main_win1)
    elif message.text == "Не оплачена":
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
        deactivate_order(user[str(message.chat.id)]["sub_id"])
        bot.send_message(message.chat.id, text = txt["msg"]["sub_check_not_found"], reply_markup=markup)
        bot.register_next_step_handler(message, main_win1)

    elif condition == False:
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
        deactivate_order(user[str(message.chat.id)]["sub_id"])
        bot.send_message(message.chat.id, text = txt["msg"]["sub_check_not_found"], reply_markup=markup)
        bot.register_next_step_handler(message, main_win1)

    elif condition == True:
        markup = types.ReplyKeyboardMarkup()
        btn1 = types.KeyboardButton(text=txt["btn"]["main_win"][0])
        btn2 = types.KeyboardButton(text=txt["btn"]["main_win"][1])
        btn3 = types.KeyboardButton(text=txt["btn"]["main_win"][2])
        markup.row(btn1, btn2, btn3)
        btn4 = types.KeyboardButton(text=txt["btn"]["main_win"][3])
        btn5 = types.KeyboardButton(text=txt["btn"]["main_win"][4])
        btn6 = types.KeyboardButton(text=txt["btn"]["main_win"][5])
        markup.row(btn4, btn5, btn6)
        bot.send_message(message.chat.id, text = txt["msg"]["sub_check_found"], reply_markup=markup)
        bot.register_next_step_handler(message, main_win1)
    else:
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
        deactivate_order(user[str(message.chat.id)]["sub_id"])
        bot.send_message(message.chat.id, text = txt["msg"]["sub_check_not_found"], reply_markup=markup)
        bot.register_next_step_handler(message, main_win1)


    
def send_mail(message):
    if str(message.text) in txt["btn"]["country"]:
        with open("user.json", 'r+', encoding='utf-8') as user:
            data = json.load(user)
        bot_trac(0, message)
        bot.send_message(message.chat.id, text = txt["msg"]["mail_text"])
        bot.register_next_step_handler(message, send_mail1, id=data[str(message.text)])
    else:
        bot.send_message(message.chat.id, text = txt["msg"]["country_choose2_er"])
        bot.register_next_step_handler(message, send_mail)

def send_mail1(message, id):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton(text=txt["btn"]["main_win"][0])
    btn2 = types.KeyboardButton(text=txt["btn"]["main_win"][1])
    btn3 = types.KeyboardButton(text=txt["btn"]["main_win"][2])
    markup.row(btn1, btn2, btn3)
    btn4 = types.KeyboardButton(text=txt["btn"]["main_win"][3])
    btn5 = types.KeyboardButton(text=txt["btn"]["main_win"][4])
    btn6 = types.KeyboardButton(text=txt["btn"]["main_win"][5])
    markup.row(btn4, btn5, btn6)
    bot_trac(0, message)
    bot.send_message(message.chat.id, text = txt["msg"]["mail_done"], reply_markup=markup)
    try:
        with open("user.json", "r", encoding='utf-8') as user:
            user = json.load(user)
        bot.send_message(id, text = txt["msg"]["mail_to"].format(by_user=str(user[str(message.chat.id)]["country"]), text = message.text)) 
    except ValueError:
        pass
    bot.register_next_step_handler(message, main_win1)


def bot_polling():
    bot.polling(none_stop=True)   
def send_daily_message():
    with open("user.json", "r", encoding='utf-8') as user:
        user = json.load(user)
    for country in txt["btn"]["country"]:
        if user[country] != 0:
            mock_message = MockMessage(chat_id=str(user[country]), text="Наступил новый {current_data} год, подведи его итог и сгенерируй событие, которое положит начало новому году".format(current_data = user["current_data"]))
            chat_gpt(mock_message)
        else:
            pass
    mock_message = MockMessage(chat_id=user[country],text="gooooool")
    with open("user.json", "r+", encoding='utf-8') as user:
        data = json.load(user)
        data["current_data"] = str(int(data["current_data"])+1)
        user.seek(0)
        json.dump(data, user, indent=4, ensure_ascii=False)
        user.truncate()


schedule.every().day.at(config_bd["news_time"]).do(send_daily_message)
if __name__ == '__main__':
    bot_thread = threading.Thread(target=bot_polling)
    bot_thread.start()
    print("Бот запущен")
    while True:
        schedule.run_pending() 
        time.sleep(1)
