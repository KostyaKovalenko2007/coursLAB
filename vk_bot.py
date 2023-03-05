import os
from random import randrange
import vk_api
import json
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor, VkKeyboardButton
from db import Client, SearchResult, Favorite, BotDB


class vkBOT():
    session = None
    def __init__(self, db):
        self.session = vk_api.VkApi(token=os.getenv('token'))
        self.longpoll = VkLongPoll(self.session)
        self.db = db

    def write_msg(self, user_id, message, keyboard=None):
        post = {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7)}
        if keyboard:
            post["keyboard"] = keyboard.get_keyboard()
        self.session.method('messages.send', post)

    def register_client_profile(self, user_id):
        vkapi = self.session.get_api()
        info = vkapi.users.get(user_ids=user_id, fields='city, sex, bdate')
        criteria = json.dumps(info[0])
        print(criteria)
        pass

    def search_by_client_criteria(self,Client_id):
        pass

    def get_next_in_searchResults(self,ClientID):

        pass

    def set_like_dislike(self,clientID,like=False):
        pass

    def run(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
               if event.to_me:
                    self.register_client_profile(event.user_id)
                    request = event.text
                    print(event.user_id, event.text)
                    if request == "start":
                        keyboard =VkKeyboard()
                        keyboard.add_button("Регистрация", VkKeyboardColor.PRIMARY, payload='{\"button\":\"1\"}')
                        keyboard.add_button("Поиск", VkKeyboardColor.POSITIVE)
                        keyboard.add_button("Выход", VkKeyboardColor.NEGATIVE)
                        self.write_msg(event.user_id, "button", keyboard)
                    elif request == "Выход":
                        keyboard =VkKeyboard(one_time=True)
                        keyboard.add_button("Пока!", VkKeyboardColor.POSITIVE)
                        keyboard.get_empty_keyboard()
                        self.write_msg(event.user_id, "button", keyboard)
                    elif request == "Поиск":
                        keyboard =VkKeyboard(inline=True)
                        keyboard.add_button("Нравится", VkKeyboardColor.POSITIVE)
                        keyboard.add_button("Не нравится", VkKeyboardColor.NEGATIVE)
                        keyboard.add_button("Следующее", VkKeyboardColor.PRIMARY)
                        self.write_msg(event.user_id, "button", keyboard)
                    elif request == "Регистрация":
                        keyboard =VkKeyboard()
                        keyboard.add_button("Введите город", VkKeyboardColor.POSITIVE)
                        keyboard.add_button("Введите возраст", VkKeyboardColor.POSITIVE)
                        self.write_msg(event.user_id, "button", keyboard)
                    elif request == "привет":
                        self.write_msg(event.user_id, f"Хай, {event.user_id}")
                    elif request == "пока":
                        self.write_msg(event.user_id, "Пока((")
                    else:
                        self.write_msg(event.user_id, "Не поняла вашего ответа...")


if __name__ == '__main__':
    bd = BotDB()
    vkbot = vkBOT(bd)
    vkbot.run()
