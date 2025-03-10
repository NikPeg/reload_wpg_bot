import requests
import uuid
import base64
import json
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
user_path = os.path.join(current_dir, "..", "user.json")
config_path = os.path.join(current_dir, "..", "config.json")

with open(config_path, 'r+', encoding='utf-8') as cfile:
        config_bd = json.load(cfile)


PUBLIC_ID = config_bd["PAYMENTS_ID"]
API_SECRET =  config_bd["PAYMENTS_TOKEN"]



def sub_check(id):
    try:
        url = "https://api.cloudpayments.ru/subscriptions/find"
        headers = {
            "Content-Type": "application/json"
        }
        auth = (PUBLIC_ID, API_SECRET)
        data = {"accountId":id}
        response = requests.post(url, headers=headers, auth=auth, data=json.dumps(data))
        response.raise_for_status()
        subscriptions_data = response.json()
        if subscriptions_data.get("Success") is False:
            return {"error": f"Ошибка при получении подписок: {subscriptions_data.get('Message')}"}
        subscriptions = subscriptions_data.get("Model")
        for subscription in subscriptions:
            if subscription.get('Status') == 'Active':
                return subscription.get('Amount'), subscription.get('Id')
        return False
    except requests.exceptions.RequestException as e:
        return {"error": f"Ошибка при выполнении запроса: {e}"}
    except json.JSONDecodeError as e:
        return {"error": f"Ошибка при разборе JSON ответа: {e}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {e}"}

def sub_pay_order(amount, id, description="Оплата подписки", order_id=None, account_id=None):
    if not order_id:
        order_id = str(uuid.uuid4())
    if not account_id:
        account_id = str(uuid.uuid4())
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
        'SubscriptionBehavior':'CreateWeekly',
        'InvoiceId': order_id,
        'AccountId': account_id
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        response_data = response.json()

        if response_data.get('Success'):
            return response_data['Model']
        else:
            return "something dont work"
    except requests.exceptions.RequestException:
        return "something dont work"

def deactivate_order(order_id):
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

if __name__ == "__main__":
    print("meow")
