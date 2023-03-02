from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from db import Client, SearchResult, Favorite, BotDB
from os import getenv


class vkBOT():
    session = None
    def __init__(self):
        self.session = vk_api.VkApi(token=getenv('token'))
        self.longpoll = VkLongPoll(self.session)

    def write_msg(self, user_id, message):
        self.session.method('messages.send',
                            {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7), })
    def get_user_profile(self,user_id):
        pass

    def run(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    request = event.text
                    print(event.user_id,event.text)
                    if request == "привет":
                        self.write_msg(event.user_id, f"Хай, {event.user_id}")
                    elif request == "пока":
                        self.write_msg(event.user_id, "Пока((")
                    else:
                        self.write_msg(event.user_id, "Не поняла вашего ответа...")


if __name__ == '__main__':
    # bd = BotDB()
    # bd.create_tables()
    vkbot = vkBOT()
    vkbot.run()
