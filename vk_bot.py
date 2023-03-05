import os
from random import randrange
import vk_api
import json
from vk_api.longpoll import VkLongPoll, VkEventType
from db import Client, SearchResult, Favorite, BotDB


class vkBOT():
    session = None
    def __init__(self, db):
        self.session = vk_api.VkApi(token=os.getenv('token'))
        self.longpoll = VkLongPoll(self.session)
        self.db = db

    def write_msg(self, user_id, message):
        self.session.method('messages.send',
                            {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7), })

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


                    if request == "привет":
                        self.write_msg(event.user_id, f"Хай, {event.user_id}")
                    elif request == "пока":
                        self.write_msg(event.user_id, "Пока((")
                    else:
                        self.write_msg(event.user_id, "Не поняла вашего ответа...")


if __name__ == '__main__':
    bd = BotDB()
    vkbot = vkBOT(bd)
    vkbot.run()
