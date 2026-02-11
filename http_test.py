"""import对请求必要的模块"""

import json
import requests


# 请求的URL和TOKEN建议在此配置
URL = "http://127.0.0.1:3000"
TOKEN = "APS"


def get_friend_list():
    """
    get_friend_list 的 Docstring
    """

    api_url = "/get_friend_list"
    full_url = f"{URL}{api_url}"

    payload = json.dumps({"no_cache": False})
    
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {TOKEN}"}
    response = requests.request("POST", full_url, headers=headers, data=payload, timeout=5)

    print(response.text)


def send_message(user_id:str , message:str):
    """
    发送消息
    """

    api_url = "/send_private_msg"
    full_url = f"{URL}{api_url}"

    payload = json.dumps(
        {"user_id": user_id, 
         "message": [{
             "type": "text",
             "data": {"text": message}
             }]
        }
    )
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {TOKEN}"}

    response = requests.request("POST", full_url, headers=headers, data=payload, timeout=5)
    json_res = response.json()
    message_id = json_res["data"]["message_id"]
    if response.status_code==200:
        print(f"Requests OK, message_id:{message_id}")


if __name__ == '__main__':
    print("This file (test.py) is not for execute.")
