import json
import os
import datetime
current_dir = os.path.dirname(os.path.abspath(__file__))
msg_path = os.path.join(current_dir, "..", "messages.json")
country_path = os.path.join(current_dir, "..", "country.json")
user_path = os.path.join(current_dir, "..", "user.json")
config_path = os.path.join(current_dir, "..", "config.json")
year_path = os.path.join(current_dir, "..", "year.json")
picture_path = os.path.join(current_dir, "..", "picture.json")


def user_requests_upgrade(id: str):
    id = str(id)
    with open(user_path, 'r+', encoding='utf-8') as ufile:
        data = json.load(ufile)
        
        # Получаем серверное время
        server_now = datetime.datetime.now()
        
        # Добавляем 3 часа для получения игрового времени
        game_now = server_now + datetime.timedelta(hours=3)
        
        # Начало игровых суток (00:00)
        game_today_start = game_now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Конвертируем обратно в серверное время для сравнения с записями
        server_today_start = game_today_start - datetime.timedelta(hours=3)
        
        with open(config_path, 'r', encoding='utf-8') as confile:
            condata = json.load(confile)
        
        max_req = condata[f"sub_lvl_req_max_{data[str(id)]['sub_lvl']}"]
        
        # Фильтруем только запросы за текущие игровые сутки
        current_day_requests = [
            req_time
            for req_time in data[str(id)]["req"]
            if datetime.datetime.fromisoformat(req_time) >= server_today_start
        ]
        
        # Полностью заменяем список запросов, удаляя все старые
        data[id]["req"] = current_day_requests
        
        # Перемещаем позицию в начало файла и обновляем данные
        ufile.seek(0)
        json.dump(data, ufile, ensure_ascii=False, indent=4)
        ufile.truncate()
        
        # Проверяем, может ли пользователь сделать запрос
        if len(current_day_requests) < max_req:
            return True
        else:
            return False


def user_new_requests(id: str):
    id = str(id)
    with open(user_path, 'r+', encoding='utf-8') as ufile:
        data = json.load(ufile)
        now = datetime.datetime.now()
        data[id]["req"].append(now.isoformat())
        ufile.seek(0)
        json.dump(data, ufile, indent=4, ensure_ascii=False)
        ufile.truncate()
        return 

def is_logged(id:str = "str please"):
    with open(user_path, 'r+', encoding='utf-8') as ufile:
        data = json.load(ufile)
        if id in data:
            return False
        else:
            return True
    
def new_year():
    with open(year_path, 'r+', encoding='utf-8') as cfile:
        data = json.load(cfile)
        data["year"] = int(data["year"])+1
        cfile.seek(0)
        json.dump(data, cfile, indent=4, ensure_ascii=False)
        cfile.truncate()
    return data["year"]

def perm_for_command(id, sub_lvl):
    with open(user_path, 'r+', encoding='utf-8') as cfile:
        data = json.load(cfile)
        if int(data[str(id)]["sub_lvl"]) >= int(sub_lvl):
            return True
        else: 
            return False
            
            



def country_upgrade(id:str = "str please", country: str = "meow"):
    new_user = True
    with open(country_path, 'r+', encoding='utf-8') as cfile:
        data = json.load(cfile)
        if data[country]["id"] == id:
            return "busy himself"
        elif data[country]["id"] != 0:
            return "busy somebody"
        for key in data:
            if data[key]["id"] == str(id):
                data[key]["id"] = 0
                new_user = False
        data[country]["id"] = str(id)
        cfile.seek(0)
        json.dump(data, cfile, indent=4, ensure_ascii=False)
        cfile.truncate()
    if new_user:
        with open(user_path, 'r+', encoding='utf-8') as ufile:
            data = json.load(ufile)
            data[id] = {
            "country":country,
            "sub_lvl":1,
            "sub_id":0,
            "id_thread":0,
            "req":[],
            "projects":{}
            }
            ufile.seek(0)
            json.dump(data, ufile, indent=4, ensure_ascii=False)
            ufile.truncate()
        return "new user"
    with open(user_path, 'r+', encoding='utf-8') as ufile:
        data = json.load(ufile)
        data[id]["country"] = country
        ufile.seek(0)
        json.dump(data, ufile, indent=4, ensure_ascii=False)
        ufile.truncate()
        return "success"



def sub_lvl_upgrade(id:str = "str please", sub: str = "meow"):
    with open(user_path, 'r+', encoding='utf-8') as ufile:
        data = json.load(ufile)
        data[id]["sub_lvl"] = sub
        ufile.seek(0)
        json.dump(data, ufile, indent=4, ensure_ascii=False)
        ufile.truncate()
    return "success"

def id_thread_upgrade(id:str = "str please", thread: str = "meow"):
    with open(user_path, 'r+', encoding='utf-8') as ufile:
        data = json.load(ufile)
        data[id]["id_thread"] = thread
        ufile.seek(0)
        json.dump(data, ufile, indent=4, ensure_ascii=False)
        ufile.truncate()
    return "success"

def sub_id_upgrade(id:str = "str please", sub_id: str = "meow"):
    with open(user_path, 'r+', encoding='utf-8') as ufile:
        data = json.load(ufile)
        data[id]["sub_id"] = sub_id
        ufile.seek(0)
        json.dump(data, ufile, indent=4, ensure_ascii=False)
        ufile.truncate()
    return "success"

def get(id, key):
    with open(user_path, 'r', encoding='utf-8') as ufile:
        data = json.load(ufile)
        return data[id][key] 

def del_user(id):
    with open(user_path, 'r+', encoding='utf-8') as ufile:
        try:
            data = json.load(ufile)
        except json.JSONDecodeError:
            data = {} 
        with open(country_path, 'r+', encoding='utf-8') as cfile:
            try:
                cdata = json.load(cfile)
            except json.JSONDecodeError:
                cdata = {}
            for key, value in cdata.items():
                if isinstance(value, dict) and "id" in value and str(value["id"]) == str(id):
                    cdata[key]["id"] = 0
                    break
            cfile.seek(0)
            json.dump(cdata, cfile, indent=4, ensure_ascii=False)
            cfile.truncate() 
        if str(id) in data: 
            del data[str(id)]
        ufile.seek(0)
        json.dump(data, ufile, indent=4, ensure_ascii=False)
        ufile.truncate()
        
def new_project(id, time, text):
    time = int(time)
    with open(year_path, 'r+', encoding='utf-8') as cfile:
        data = json.load(cfile)
        present_time = data["year"]
    with open(user_path, 'r+', encoding='utf-8') as ufile:
        data = json.load(ufile)
        time = str(present_time+time)
        data[id]["projects"][str(time)] = text
        ufile.seek(0)
        json.dump(data, ufile, indent=4, ensure_ascii=False)
        ufile.truncate()
    return "success"

def get_graph_history(country):
    with open(country_path, 'r+', encoding='utf-8') as cfile:
        data = json.load(cfile)
        mdata = data[country]
        del mdata["id"]
        return mdata


translate = ["GDP", "population", "rating_government", "power"]


def mod_graph(country, d):
    with open(country_path, 'r+', encoding='utf-8') as cfile:
        data = json.load(cfile)
        for i, value in enumerate(d.values()):
            key = translate[i]
            if type(value) == 'list':
                data[country][key].append(int(value[0]))
                continue
            if isinstance(value, str):
                value = value.split()[0]
            data[country][key].append(float(value))
        cfile.seek(0)
        json.dump(data, cfile, indent=4, ensure_ascii=False)
        cfile.truncate()


def change_photo(key, value):
    with open(picture_path, 'r+', encoding='utf-8') as pfile:
        data = json.load(pfile)
        key = key.replace("/", "")
        data[key] = value
        pfile.seek(0)
        json.dump(data, pfile, indent=4, ensure_ascii=False)
        pfile.truncate()
    return "success"

def del_proj(id, key):
    with open(user_path, 'r+', encoding='utf-8') as ufile:
        data = json.load(ufile)
        del data[str(id)]["projects"][key]
        ufile.seek(0)
        json.dump(data, ufile, indent=4, ensure_ascii=False)
        ufile.truncate()

def get_photo(photo:str):
    with open(picture_path, 'r+', encoding='utf-8') as pfile:
        data = json.load(pfile)
        if data[photo] == 0:
            return open(f"{photo}.png", 'rb')
        else:
            return data[photo]






if __name__ == "__main__":
    print(user_requests_upgrade("6532830698"))
    user_new_requests("6532830698")
