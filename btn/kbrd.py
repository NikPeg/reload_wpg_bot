import os
import json
import telebot
from telebot import types

current_dir = os.path.dirname(os.path.abspath(__file__))
msg_path = os.path.join(current_dir, "..", "messages.json")
with open(msg_path, "r", encoding='utf-8') as message:
    txt = json.load(message)

def main_menu():
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton(text=txt["btn"]["main_win"][0])
    btn2 = types.KeyboardButton(text=txt["btn"]["main_win"][1])
    btn3 = types.KeyboardButton(text=txt["btn"]["main_win"][2])
    markup.row(btn1, btn2, btn3)
    btn4 = types.KeyboardButton(text=txt["btn"]["main_win"][3])
    btn5 = types.KeyboardButton(text=txt["btn"]["main_win"][4])
    btn6 = types.KeyboardButton(text=txt["btn"]["main_win"][5])
    markup.row(btn4, btn5, btn6)
    return markup

def main_win_reg_nl1():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text=txt["btn"]["start1"], url = txt["btn"]["start1_url"])
    markup.add(btn1)
    return markup

def main_win_reg_nl2():
    markup = types.ReplyKeyboardMarkup()
    btn2 = types.KeyboardButton(txt["btn"]["start2"])
    markup.add(btn2)
    return markup

def country_list():
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton(text=txt["btn"]["country"][0])
    btn2 = types.KeyboardButton(text=txt["btn"]["country"][1])
    btn3 = types.KeyboardButton(text=txt["btn"]["country"][2])
    markup.row(btn1, btn2, btn3)
    btn4 = types.KeyboardButton(text=txt["btn"]["country"][3])
    btn5 = types.KeyboardButton(text=txt["btn"]["country"][4])
    btn10 = types.KeyboardButton(text=txt["btn"]["country"][9])
    btn6 = types.KeyboardButton(text=txt["btn"]["country"][5])
    markup.row(btn4, btn5, btn6, btn10)
    btn7 = types.KeyboardButton(text=txt["btn"]["country"][6])
    btn8 = types.KeyboardButton(text=txt["btn"]["country"][7])
    btn9 = types.KeyboardButton(text=txt["btn"]["country"][8])
    markup.row(btn7, btn8, btn9)
    return markup


def sub():
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton(txt["btn"]["sub"][0])
    btn2 = types.KeyboardButton(txt["btn"]["sub"][1])
    btn3 = types.KeyboardButton(txt["btn"]["sub"][2])
    markup.add(btn1, btn2, btn3)
    return markup
def sub_check():
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton(txt["btn"]["sub_found"])
    markup.add(btn1)
    return markup


if __name__ == "__main__":
    pass