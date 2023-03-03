from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from db import Client, SearchResult, Favorite, BotDB
from os import getenv


class vkBOT():
    session = None
    api = None
    db: BotDB = None
    def __init__(self, db:BotDB):
        self.session = vk_api.VkApi(token=getenv('token'))
        self.longpoll = VkLongPoll(self.session)
        self.db = db
        self.api = self.session.get_api()

    def write_msg(self, user_id, message):
        self.session.method('messages.send',
                            {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7), })

    def register_client_profile(self,user_id):
        #нужно по ID вытащить критерии поиска
        #
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
                    request = event.text
                    print(event.user_id,event.text)
                    if request == "привет":
                        self.write_msg(event.user_id, f"Хай, {event.user_id}")
                    elif request == "пока":
                        self.write_msg(event.user_id, "Пока((")
                    else:
                        self.write_msg(event.user_id, "Не поняла вашего ответа...")


if __name__ == '__main__':
    bd = BotDB()
    bd.create_tables()
    vkbot = vkBOT(bd)
    vkbot.run()
