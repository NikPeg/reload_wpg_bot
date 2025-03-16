import json
import openai
import telebot
import time
import schedule
import threading
import btn
import bd
import gpt
import sub
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import io
import numpy as np
import logging
import traceback 
import random
import string

logging.basicConfig(filename="error.log", level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

msg_path = "messages.json"
country_path = "country.json"
user_path = "user.json"
config_path = "config.json"
year_path = "year.json"
picture_path = "picture.json"



with open(config_path, "r", encoding='utf-8') as config:
    config_bd = json.load(config)
bot = telebot.TeleBot(config_bd["tg_token"])
openai.api_key = config_bd["chatGPT_token"]
PUBLIC_ID = config_bd["PAYMENTS_ID"]
API_SECRET =  config_bd["PAYMENTS_TOKEN"]
DEBUG = bool(config_bd["debug"])
with open(msg_path, "r", encoding='utf-8') as messages:
    txt = json.load(messages)

def bot_trac(message):
        if DEBUG:
            bot.forward_message(chat_id = -4707616830, from_chat_id = message.chat.id, message_id = message.message_id)      



@bot.message_handler(func=lambda message: str(message.chat.id) in config_bd["admin_list"] and message.text.lower() in ["new_year", "/new_year"])
def admin_new_year(message):
    year = new_year()
    markup = btn.main_menu()
    message = bot.send_message(message.chat.id, text = txt["msg"]["admin_new_year"].format(year = year), reply_markup=markup)


@bot.message_handler(func=lambda message: str(message.chat.id) in config_bd["admin_list"] and message.text.lower() in ["answer", "/answer"])
def send_admin_mail(message):
    markup = btn.country_list() 
    message = bot.send_message(message.chat.id, text = txt["msg"]["mail"], reply_markup=markup)
    bot.register_next_step_handler(message, send_admin_mail1)


def send_admin_mail1(message):
    if message.text in txt["btn"]["country"]:
        with open(country_path, 'r+', encoding='utf-8') as user:
            data = json.load(user)
        country = message.text
        message = bot.send_message(message.chat.id, text = txt["msg"]["mail_text"])
        bot.register_next_step_handler(message, send_admin_mail2, recipient=data[country]["id"])
    else:
        markup = btn.country_list() 
        message = bot.send_message(message.chat.id, text = txt["msg"]["country_choose2_er"], reply_markup = markup)
        bot.register_next_step_handler(message, send_admin_mail1)
def send_admin_mail2(message, recipient): 
    markup = btn.main_menu()
    bot.send_message(message.chat.id, text = txt["msg"]["mail_done"], reply_markup=markup)
    try:
        with open(user_path, "r", encoding='utf-8') as user1:
            user = json.load(user1)
        message = bot.send_message(recipient, text = txt["msg"]["admin_mail_to"].format(by_user=str(user[recipient]["country"]), text = message.text)) 
    except:
        pass



@bot.message_handler(func=lambda message: str(message.chat.id) in config_bd["admin_list"] and message.text.lower() in ["unsub", "/unsub"])
def unsub(message):
    markup = btn.country_list()
    message = bot.send_message(message.chat.id, text = txt["msg"]["admin_unsub"], reply_markup=markup)
    bot.register_next_step_handler(message, unsub2)

def unsub2(message):
    with open(country_path, "r+", encoding='utf-8') as file:
        data = json.load(file)
    bd.del_user(data[message.text]["id"])
    markup = btn.main_menu()
    message = bot.send_message(message.chat.id, text = txt["msg"]["admin_done"], reply_markup=markup)

@bot.message_handler(func=lambda message: str(message.chat.id) in config_bd["admin_list"] and message.text.lower() in ["mailing", "/mailing"])
def mailing(message):
    message = bot.send_message(message.chat.id, text = txt["msg"]["admin_mailing"])
    bot.register_next_step_handler(message, mailing1)
def mailing1(message):
    with open(country_path, "r+", encoding='utf-8') as file:
        data = json.load(file)
        for country in data:
            leader = data[country]["id"]
            if leader == 0:
                pass
            else:
                message = bot.send_message(leader, text = message.text)
                bot.send_message(chat_id = -4707616830, text = f"Отправлено в {country}")

@bot.message_handler(content_types=['photo'], func=lambda message: str(message.chat.id) in config_bd["admin_list"] and message.caption is not None and message.caption.lower() in ["map", "/map"])
def map_change(message):
    bot_trac(message)
    bd.change_photo(message.caption.lower(), message.photo[-1].file_id)
    message = bot.send_message(message.chat.id, text = txt["msg"]["admin_done"], reply_markup= btn.main_menu())


@bot.message_handler(func=lambda message: message.chat.id == -4707616830)
def i_hate(message):
    pass


@bot.message_handler(func=lambda message: bd.is_logged(str(message.chat.id)))
def new_user(message):
    markup = btn.main_win_reg_nl1()
    message = bot.send_message(message.chat.id, txt["msg"]["start1"] , reply_markup=markup)
    markup = btn.main_win_reg_nl2()
    message = bot.send_message(message.chat.id, txt["msg"]["start2"], reply_markup=markup)
    bot.register_next_step_handler(message, country_choose)


@bot.message_handler(func=lambda message: "страна" == message.text.lower())
def country_choose(message):
    bot_trac(message)
    markup = btn.country_list()
    message = bot.send_message(message.chat.id, text = txt["msg"]["country_choose"], reply_markup=markup)
    bot_trac(message)
    bot.register_next_step_handler(message, country_choose2)


def country_choose2(message):
    bot_trac(message)
    if str(message.text) in txt["btn"]["country"]:
        refund = bd.country_upgrade(str(message.chat.id), message.text)
        if refund == "busy himself":
            markup = btn.main_menu()
            message = bot.send_message(message.chat.id, txt["msg"]["country_choose2_himself"].format(country=message.text), reply_markup=markup)
            bot_trac(message)
            
        if refund == "success":
            thread = gpt.user_get_thread()
            bd.id_thread_upgrade(str(message.chat.id), thread)
            markup = btn.main_menu()
            with open(user_path, "r", encoding='utf-8') as user:
                user = json.load(user)
            message = bot.send_message(message.chat.id, text = txt["msg"]["country_choose2"].format(name=str(message.from_user.first_name), country=message.text), reply_markup=markup)
            bot_trac(message)
        elif refund == "busy somebody":
            markup = btn.country_list()
            message = bot.send_message(message.chat.id, txt["msg"]["country_choose2_busy"].format(country=message.text), reply_markup=markup)
            bot_trac(message)
            bot.register_next_step_handler(message, country_choose2)
        elif refund == "new user":
            with open(user_path, 'r+', encoding='utf-8') as user:
                data = json.load(user)
            thread = gpt.user_get_thread()
            bd.id_thread_upgrade(str(message.chat.id), thread = thread)
            with open("sub.png", 'rb') as photo:
                markup = btn.sub()
                bot.send_photo(message.chat.id, photo, reply_markup=markup)
            message = bot.send_message(message.chat.id, text = txt["msg"]["country_choose2"].format(name=str(message.from_user.first_name), country=message.text), reply_markup=markup)
            bot_trac(message)
            bot.register_next_step_handler(message, sub2, new_user=True)
    else:
        markup = btn.country_list()
        message = bot.send_message(message.chat.id, text = txt["msg"]["country_choose2_er"], reply_markup=markup)
        bot.register_next_step_handler(message, country_choose2)

@bot.message_handler(func=lambda message: "погружение" == message.text.lower())
def sub1(message):
    bot_trac(message)
    markup = btn.sub()
    bot.send_photo(message.chat.id, bd.get_photo("sub"), reply_markup=markup)
    bot.register_next_step_handler(message, sub2)


def sub2(message, new_user = False):
    if message.text in txt["btn"]["sub"]:
        if message.text.lower() == "i уровень":
            bot_trac(message)
            markup = btn.main_menu()
            bd.sub_lvl_upgrade(str(message.chat.id), "1")
            message = bot.send_message(message.chat.id, text = txt["msg"]["sub_done"].format(sub_lvl = "1"), reply_markup = markup)
            bot_trac(message)
            if new_user:
                message = bot.send_message(message.chat.id, text = txt["msg"]["reg_success"], reply_markup = markup)
            
        if message.text.lower() == "ii уровень":
            bot_trac(message)
            markup = btn.sub_check()
            amount = config_bd["sub_lvl2_price"]
            order = sub.sub_pay_order(amount=amount, id=str(message.chat.id), order_id=str(message.chat.id), account_id=str(message.chat.id))
            bd.sub_id_upgrade(str(message.chat.id), order.get('Id'))
            message = bot.send_message(message.chat.id, text = txt["msg"]["sub"].format(url = order.get('Url')), reply_markup = markup)
            bot_trac(message)
            bot.register_next_step_handler(message, sub3, new_user)
        if message.text.lower() == "iii уровень":
            bot_trac(message)
            markup = btn.sub_check()
            amount = config_bd["sub_lvl3_price"]
            order = sub.sub_pay_order(amount=amount, id=str(message.chat.id), order_id=str(message.chat.id), account_id=str(message.chat.id))
            bd.sub_id_upgrade(str(message.chat.id), order.get('Id'))
            message = bot.send_message(message.chat.id, text = txt["msg"]["sub"].format(url = order.get('Url')), reply_markup = markup)
            bot_trac(message)
            bot.register_next_step_handler(message, sub3, new_user)
    else:
        bot_trac(message)
        markup = btn.main_menu()
        message = bot.send_message(message.chat.id, text = txt["msg"]["sub_err"], reply_markup = markup)
        bot_trac(message)
        if new_user:
            message = bot.send_message(message.chat.id, text = txt["msg"]["reg_success"], reply_markup = markup)
            

def sub3(message, new_user):
    bot_trac(message)
    cheque = sub.sub_check(str(message.chat.id))
    if cheque != False:
        if cheque[0] == config_bd["sub_lvl2_price"]:
            bd.sub_lvl_upgrade(str(message.chat.id), '2')
            bd.sub_id_upgrade(str(message.chat.id), cheque[1])
            markup = btn.main_menu()
            message = bot.send_message(message.chat.id, text = txt["msg"]["sub_check_found"].format(sub_lvl = "2"), reply_markup = markup)
            bot_trac(message)
            if new_user:
                message = bot.send_message(message.chat.id, text = txt["msg"]["reg_success"], reply_markup = markup)
        elif cheque[0] == config_bd["sub_lvl3_price"]:
            bd.sub_id_upgrade(str(message.chat.id), cheque[1])
            bd.sub_lvl_upgrade(str(message.chat.id), '3')
            markup = btn.main_menu()
            message = bot.send_message(message.chat.id, text = txt["msg"]["sub_check_found"].format(sub_lvl = "3"), reply_markup = markup)
            bot_trac(message)
            if new_user:
                message = bot.send_message(message.chat.id, text = txt["msg"]["reg_success"], reply_markup = markup)
        else: 
            order_id = bd.get(str(message.chat.id), "sub_id")
            sub.deactivate_order(order_id)
            markup = btn.main_menu()
            message = bot.send_message(message.chat.id, text = txt["msg"]["sub_check_not_found"], reply_markup = markup)
            bot_trac(message)
            if new_user:
                message = bot.send_message(message.chat.id, text = txt["msg"]["reg_success"], reply_markup = markup)
    else:
        order_id = bd.get(str(message.chat.id), "sub_id")
        sub.deactivate_order(order_id)
        markup = btn.main_menu()
        message = bot.send_message(message.chat.id, text = txt["msg"]["sub_check_not_found"], reply_markup = markup)
        bot_trac(message)
        if new_user:
                message = bot.send_message(message.chat.id, text = txt["msg"]["reg_success"], reply_markup = markup)



@bot.message_handler(func=lambda message: "телеграмма" == message.text.lower() and not bd.perm_for_command(str(message.chat.id), 2))
def send_graphics_without_perm(message):
    markup = btn.main_menu()
    message = bot.send_message(message.chat.id, text = txt["msg"]["small_sub_2"], reply_markup=markup)
    bot_trac(message)


@bot.message_handler(func=lambda message: "телеграмма" == message.text.lower() and bd.perm_for_command(str(message.chat.id), 2))
def send_mail(message):
    bot_trac(message)
    markup = btn.country_list() 
    message = bot.send_message(message.chat.id, text = txt["msg"]["mail"], reply_markup=markup)
    bot_trac(message)
    bot.register_next_step_handler(message, send_mail1)

def send_mail1(message):
    bot_trac(message)
    if message.text in txt["btn"]["country"]:
        with open(country_path, 'r+', encoding='utf-8') as user:
            data = json.load(user)
        country = message.text
        message = bot.send_message(message.chat.id, text = txt["msg"]["mail_text"])
        bot_trac(message)
        bot.register_next_step_handler(message, send_mail2, recipient=data[country]["id"])
    else:
        markup = btn.country_list() 
        message = bot.send_message(message.chat.id, text = txt["msg"]["country_choose2_er"], reply_markup = markup)
        bot_trac(message)
        bot.register_next_step_handler(message, send_mail1)

def send_mail2(message, recipient): 
    bot_trac(message)
    markup = btn.main_menu()
    bot.send_message(message.chat.id, text = txt["msg"]["mail_done"], reply_markup=markup)
    
    try:
        with open(user_path, "r", encoding='utf-8') as user:
            user = json.load(user)
        message = bot.send_message(recipient, text = txt["msg"]["mail_to"].format(by_user=str(user[str(message.chat.id)]["country"]), text = message.text)) 
        bot_trac(message)
    except:
        pass


@bot.message_handler(func=lambda message: "проекты" == message.text.lower())
def project(message):
    with open(user_path, "r", encoding='utf-8') as user:
        user = json.load(user)
    text = ""
    if len(user[str(message.chat.id)]["projects"]) == 0:
        markup = btn.main_menu()
        bot.send_message(message.chat.id, text = txt["msg"]["proj_empty"], reply_markup=markup)
        return
    text = ""
    i = 1
    for proj, order in user[str(message.chat.id)]["projects"].items():
        order = " ".join(order.split()[:10])
        text = text + f"\n{i}. {order}...\nДата окончания: {proj} год"
        i += 1
    markup = btn.main_menu()
    message = bot.send_message(message.chat.id, text = txt["msg"]["proj_list"].format(text = text), reply_markup=markup)
    bot_trac(message)

@bot.message_handler(func=lambda message: "графики" == message.text.lower() and not bd.perm_for_command(str(message.chat.id), 3))
def send_graphics_without_perm(message):
    markup = btn.main_menu()
    message = bot.send_message(message.chat.id, text = txt["msg"]["small_sub_3"], reply_markup=markup)
    bot_trac(message)

@bot.message_handler(func=lambda message: "графики" == message.text.lower() and bd.perm_for_command(str(message.chat.id), 3))
def send_graphics(message):
    with open(user_path, "r", encoding='utf-8') as user:
        user = json.load(user)
    data = bd.get_graph_history(user[str(message.chat.id)]["country"])
    for key in data:
        y_values = data[key]
        x_values = np.arange(2567, 2567 + len(y_values))
        plt.figure(figsize=(8, 6))
        plt.plot(x_values, y_values, marker='o')  
        plt.xlabel("Год")
        if key == "GDP":
            y_text = "Млрд паромонет"
            name = "ВВП"
        if key == "population":
            y_text = "Млн человек"
            name = "Население"
        if key == "rating_government":
            y_text = "% населения"
            name = "Процент поддержки правительства"
        plt.ylabel(y_text)
        plt.title(name)
        plt.grid(True)  
        formatter = ticker.FuncFormatter(lambda x, pos: f"{int(x)}")
        plt.gca().xaxis.set_major_formatter(formatter)
        plt.ylim(min(y_values) - 0.1 * abs(min(y_values)), max(y_values) + 0.1 * abs(max(y_values)))
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        graph = buf.read()
        message = bot.send_photo(message.chat.id, graph)
        bot_trac(message)
        plt.close()
        plt.clf()    


@bot.message_handler(func=lambda message: "карта" == message.text.lower())
def send_map(message):
    bot_trac(message)
    markup = btn.main_menu()
    bot.send_photo(message.chat.id, bd.get_photo("map"))
    bot.send_photo(message.chat.id, bd.get_photo("land_form"), reply_markup=markup)


@bot.message_handler(func=lambda message: len(message.text.split()) == 1)
def unknow_command(message):
    markup = btn.main_menu()
    message = bot.send_message(message.chat.id, text = txt["msg"]["unknown_text"], reply_markup=markup)


def get_user_info(user_country, years=0):
    success = random.randrange(1, 101)
    data = bd.get_graph_history(user_country)
    gdp = data["GDP"][-1]
    population = data["population"][-1]
    support = data["rating_government"][-1]
    era = config_bd["era"]

    res = (
        f"ВВП: {gdp} млрд паромонет\n"
        f"Население: {population} млн человек\n"
        f"Поддержка населения: {support}%\n"
        f"Эпоха: {era}\n"
    )
    if years == 0 or years == 999:
        res += f"Кубик: {success}% (используй эту информацию, но не упомянай бросок кубика в результате приказа!)\n"
    elif years != 999:
        res += f"Срок реализации: {years} лет\n"
    bot.send_message(-4707616830, text=res)
    return res


def check_years(text, thread):
    era = config_bd["era"]
    answer = gpt.ask(f"Это сообщение игрока в военно-политическую игру:\n{text}\nНапиши срок реализации приказа игрока в эпохе {era}. Ответь числом от 0 до 100 лет. Если сообщение игрока является вопросом, ответь 999. Объясни свой ответ")
    bot.send_message(-4707616830, text=answer)
    for word in answer.split()[::-1]:
        if "-" in word:
            word = word.split("-")[0]
        word = word.translate(str.maketrans('', '', string.punctuation))
        if word.isdigit():
            bot.send_message(-4707616830, text="Parsed answer: " + word)
            return int(word)
    return 999


@bot.message_handler(func=lambda message: bd.user_requests_upgrade(message.chat.id))
def to_gpt(message):
    handle_gpt_message(message)


def handle_gpt_message(message, text=None):
    if not text:
        bot_trac(message)
    separator = "\n\n"
    if not text and separator in message.text:
        parts = message.text.split(separator)
        for part in parts:
            handle_gpt_message(message, text=part)
        return
    elif not text:
        text = message.text

    for_edit = bot.send_message(message.chat.id, text=txt["msg"]["gpt_thinks"])
    with open(user_path, 'r+', encoding='utf-8') as user:
        data = json.load(user)
    user_country = data[str(message.chat.id)]["country"]
    user_thread = data[str(message.chat.id)]["id_thread"]
    answer = "Произошла ошибка. Пожалуйста, повторите запрос!"
    years = check_years(text, user_thread)
    info = get_user_info(user_country, years)
    text = gpt.chat_gpt(thread = user_thread, text = f"Я, повелитель {user_country}, приказываю {text}\n{info}", assist_id=config_bd["user_event_handler"])
    bd.user_new_requests(str(message.chat.id))
    bot.edit_message_text(chat_id=for_edit.chat.id, message_id = for_edit.message_id, text = text)
    bot_trac(for_edit)
    
    if years > 0 and years != 999:
        bd.new_project(id = str(message.chat.id), time = years, text = text)
        message = bot.send_message(chat_id=for_edit.chat.id, text=f"Проект начат. Срок реализации: {years} лет")
        bot_trac(message)
        return
    if years == 999:
        return 

    text = gpt.country_report(thread_id=user_thread, assist_id= config_bd["country_report"], country = user_country, text = f"Лидер {user_country} приказал {text}")
    if not text:
        bot.send_message(-4707616830, "Ассистент влияния на страны молчит")
        return
    json_string = text.replace("json", "")
    json_string = json_string.replace("```", "").strip()
    json_string = json.loads(json_string)
    print(json_string)
    with open(country_path, 'r+', encoding='utf-8') as country:
        country_list = json.load(country)
    for country in json_string:
        print(country)
        if country == user_country:
            continue
        if country in country_list and isinstance(country_list[country], dict) and "id" in country_list[country]:
            country_data = country_list[country]
            if country_data["id"] != 0:
                id = int(country_data["id"])
                message = bot.send_message(id, text = json_string[country])
                bot.send_message(-4707616830, f"Влияние на срану {country}:")
                bot_trac(message)


@bot.message_handler(func=lambda message: True)
def to_gpt(message):
    markup = btn.main_menu()
    message = bot.send_message(message.chat.id, text = txt["msg"]["max_req"], reply_markup=markup)


def bot_polling():
    bot.polling(none_stop=True)   


def new_year():
    with open(country_path, 'r+', encoding='utf-8') as country:
        country_list = json.load(country)
    with open(user_path, 'r+', encoding='utf-8') as user:
        user_list = json.load(user)
    year = bd.new_year()
    for country in country_list:
        id = int(country_list[country]["id"])
        if id != 0:
            with open(user_path, 'r+', encoding='utf-8') as user:
                data = json.load(user)
            user_thread = data[str(id)]["id_thread"]
            time.sleep(1)
            try:
                era = config_bd["era"]
                info = get_user_info(country)
                answer = gpt.chat_gpt(thread = user_thread, text = f"Напиши список главных новостей, произошедших за последний год в стране {country}, пиши кратко и по пунктам. Пиши реалистичные новости для эпохи {era}, не только хорошие новости.\n{info}", assist_id=config_bd["user_event_handler"])
                message = bot.send_message(id, text = f"{country} встретил(а) новый {year} год следующей новостью: \n {answer}")
                bot_trac(message)
                
                graph = gpt.ask(f"Проанализируй эти новости: {answer}\n{info}\nНапиши новые показатели ВВП, численности и поддержки населения на основе этих данных. Дай ответ в формате json. Пришли только json с новыми показателями без комментариев")
                message = bot.send_message(id, "Новые показатели:\n" + graph)
                bot_trac(message)
                json_string = graph.replace("json", "")
                json_string = json_string.replace("```", "").strip()
                graph = json.loads(json_string)
                bd.mod_graph(country, graph)
            except Exception as e:
                logging.error(f"Произошла ошибка: {type(e).__name__} - {e}\n{traceback.format_exc()}")
                print("Произошла ошибка. Подробности записаны в error.log")
            if len(user_list[str(id)]["projects"]) > 0:
                for proj in user_list[str(id)]["projects"]:
                    if int(proj) <= int(year):
                        try:
                            info = get_user_info(country)
                            text = gpt.chat_gpt(thread = user_thread, text = f"В стране {country} завершен проект, обьявленный приказом:\n{user_list[str(id)]["projects"][proj]}\n{info}", assist_id=config_bd["user_event_handler"])
                            message = bot.send_message(id, text)
                            bot_trac(message)
                            bd.del_proj(str(id), proj)
                            text = gpt.country_report(thread_id=user_thread, assist_id= config_bd["country_report"], country = country, text = f"Лидер {country} приказал {message.text}. Проект уже завершен")
                            if not text:
                                bot.send_message(-4707616830, "Ассистент влияния на страны молчит")
                                continue
                            json_string = text.replace("json", "")
                            json_string = json_string.replace("```", "").strip()
                            json_string = json.loads(json_string)
                            with open(country_path, 'r+', encoding='utf-8') as country:
                                country_list = json.load(country)
                            for new_country in json_string:
                                if new_country == country:
                                    continue
                                if new_country in country_list and isinstance(country_list[new_country], dict) and "id" in country_list[new_country]:
                                    country_data = country_list[new_country]
                                    if country_data["id"] != 0:
                                        id = int(country_data["id"])
                                        message = bot.send_message(id, text = json_string[new_country])
                                        bot.send_message(-4707616830, f"Влияние на страну {new_country}:")
                                        bot_trac(message)
                        except Exception as e:
                            logging.error(f"Произошла ошибка: {type(e).__name__} - {e}\n{traceback.format_exc()}")
                            print("Произошла ошибка. Подробности записаны в error.log")
    return year


schedule.every().day.at(config_bd["new_year"]).do(new_year)
if __name__ == '__main__':
    bot_thread = threading.Thread(target=bot_polling)
    bot_thread.start()
    print("Бот запущен")
    while True:
        schedule.run_pending() 
        time.sleep(1)
