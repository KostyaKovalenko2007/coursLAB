import os
from random import randrange
import vk_api
import json
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor, VkKeyboardButton
from db import BotDB
from os import getenv
import requests


class vkBOT():
    #test changes
    session = None
    api = None
    db: BotDB = None
    sex = {1: 'Женский', 2: 'Мужской'}
    priv_api = None

    def __init__(self, db: BotDB):
        self.session = vk_api.VkApi(token=getenv('token'))
        self.longpoll = VkLongPoll(self.session)
        self.db: BotDB = db
        self.vk = self.session.get_api()
        self.api = self.session.get_api()
        self.priv_api = vk_api.VkApi(token=getenv('priv_token')).get_api()
        self.upload = vk_api.VkUpload(vk_api.VkApi(token=getenv('priv_token')))

    def send_profile(self, user_id, profile: dict, keyboard):
        fotos = []
        if profile.get('img1') != None:
            fotos.append(profile.get('img1'))
        if profile.get('img2') != None:
            fotos.append(profile.get('img2'))
        if profile.get('img3') != None:
            fotos.append(profile.get('img3'))
        message = f"{profile.get('fio')} {profile.get('profile')}"

        attachments = []
        session = requests.Session()
        for foto in fotos:
            try:
                image = session.get(foto, stream=True)
                photo = self.upload.photo_messages(photos=image.raw)[0]
                attachments.append('photo{}_{}_{}'.format(photo['owner_id'], photo['id'], photo['access_key']))
            except:
                pass
        post = {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7),
                'attachment': ','.join(attachments)}
        if keyboard:
            post["keyboard"] = keyboard.get_keyboard()
        self.session.method('messages.send', post)

    def write_msg(self, user_id, message, keyboard=None):
        post = {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7)}
        if keyboard:
            post["keyboard"] = keyboard.get_keyboard()
        self.session.method('messages.send', post)

    def register_client_profile(self, user_id):
        info = self.api.users.get(user_ids=user_id, fields='city, sex, bdate')[0]
        bot_user = {'id': info['id'],
                    'citi_id': info['city']['id'],
                    'city_title': info['city']['title'],
                    'sex': info['sex'],
                    'bdate': info.get('bdate'),
                    'first_name': info['first_name'],
                    'last_name': info['last_name'],
                    'can_access_closed': info['can_access_closed']}
        if bot_user['sex'] == 1:
            bot_user['sex_find'] = 2
        else:
            bot_user['sex_find'] = 1

        if bot_user['bdate'] != None:
            bot_user_bdate = bot_user['bdate'].split('.')
        else:
            bot_user_bdate = [1, 1, 2000]

        # Укажем критерии поиска людей +/-10 лет, если указан возраст
        if len(bot_user_bdate) == 3:
            bot_user['age_from'] = 2023 - bot_user_bdate[2] - 10
            if bot_user['age_from'] < 18:
                bot_user['age_from'] = 18
            bot_user['age_to'] = bot_user['age_from'] + 10
        else:
            bot_user['age_from'] = 18
            bot_user['age_to'] = 40

        result, msg = self.db.create_client(vkID=user_id, creteria=json.dumps(bot_user))
        print(msg)
        return result

    def search_by_client_criteria(self, Client_id):
        # делает выборку/поиск из VK, результат кладет в базу

        creteria = self.db.get_client_criterias(vkID=Client_id)

        params = {'count': 20,
                  'city': creteria['citi_id'],
                  'sex': creteria['sex_find'],
                  'age_from': creteria['age_from'],
                  'age_to': creteria['age_to'],
                  'fields': 'can_write_private_message',
                  'has_photo': 1}
        users = self.priv_api.users.search(**params)
        search_list = []
        for user in users['items']:
            photos = self.get_user_photos(vkID=user['id'])
            if photos != []:
                search_list.append({'id': user['id'],
                                    'first_name': user['first_name'],
                                    'last_name': user['last_name'],
                                    'photos': photos
                                    })
        self.db.put_search(ClientID=Client_id, SearchResults=search_list)

    def get_next_in_searchResults(self, ClientID):
        # возвращает следующий профиль из поисковых результатов
        return self.db.get_next_profile(client=self.db.get_client_by_vkID(vkID=ClientID))

    def get_profile_by_searchID(self,id:int):
        pass

    def set_like_dislike(self, clientID, like=False):
        client = self.db.get_client_by_vkID(vkID=clientID)
        self.db.set_like(client=client, like=like)
        pass
#TODO  Вывести список избранных людей.
    def run(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    request = event.text
                    print(event.user_id, event.text)
                    if request == "start":
                        keyboard = VkKeyboard()
                        keyboard.add_button("Регистрация", VkKeyboardColor.PRIMARY, payload='{\"button\":\"1\"}')
                        keyboard.add_button("Поиск", VkKeyboardColor.POSITIVE)
                        keyboard.add_button("Выход", VkKeyboardColor.NEGATIVE)
                        self.write_msg(event.user_id, "button", keyboard)
                    elif request == "Выход":
                        keyboard = VkKeyboard(one_time=True)
                        keyboard.add_button("Пока!", VkKeyboardColor.POSITIVE)
                        keyboard.get_empty_keyboard()
                        self.write_msg(event.user_id, "button", keyboard)
                    elif request == "Поиск":
                        self.search_by_client_criteria(Client_id=event.user_id)
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button("Нравится", VkKeyboardColor.POSITIVE)
                        keyboard.add_button("Не нравится", VkKeyboardColor.NEGATIVE)
                        keyboard.add_button("Следующее", VkKeyboardColor.PRIMARY)
                        self.send_profile(event.user_id, self.get_next_in_searchResults(ClientID=event.user_id),
                                          keyboard)
                    elif request == "Регистрация":
                        res, msg = self.register_client_profile(user_id=event.user_id)
                        if res:
                            info = self.db.get_client_criterias(vkID=str(event.user_id))
                            keyboard = VkKeyboard()
                            self.write_msg(event.user_id, "Вас зарегистрировали", None)
                            self.write_msg(event.user_id,
                                           "Ваши поисковые критерии:\n" \
                                           f"Город: {info.get('city_title')}\n" \
                                           f"Пол: {self.sex[info.get('sex_find')]}\n" \
                                           f"Возраст c: {info.get('age_from')}\n" \
                                           f"Возраст по: {info.get('age_to')}", None)
                        else:
                            info = self.db.get_client_criterias(vkID=str(event.user_id))
                            keyboard = VkKeyboard()
                            self.write_msg(event.user_id, "Вы уже были зарегистрированы", None)
                            self.write_msg(event.user_id,
                                           "Ваши поисковые критерии:\n" \
                                           f"Город: {info.get('city_title')}\n" \
                                           f"Пол: {self.sex[info.get('sex_find')]}\n" \
                                           f"Возраст c: {info.get('age_from')}\n" \
                                           f"Возраст по: {info.get('age_to')}", None)

                    elif request == "Следующее":
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button("Нравится", VkKeyboardColor.POSITIVE)
                        keyboard.add_button("Не нравится", VkKeyboardColor.NEGATIVE)
                        keyboard.add_button("Следующее", VkKeyboardColor.PRIMARY)
                        self.send_profile(event.user_id, self.get_next_in_searchResults(ClientID=event.user_id),
                                          keyboard)
                    elif request == "Нравится":
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button("Нравится", VkKeyboardColor.POSITIVE)
                        keyboard.add_button("Не нравится", VkKeyboardColor.NEGATIVE)
                        keyboard.add_button("Следующее", VkKeyboardColor.PRIMARY)
                        self.set_like_dislike(clientID=event.user_id, like=True)
                    elif request == "Не нравится":
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button("Нравится", VkKeyboardColor.POSITIVE)
                        keyboard.add_button("Не нравится", VkKeyboardColor.NEGATIVE)
                        keyboard.add_button("Следующее", VkKeyboardColor.PRIMARY)
                        self.set_like_dislike(clientID=event.user_id, like=False)
                    else:
                        self.write_msg(event.user_id, "Команда не распознана начните с команды 'start'")

    def get_user_photos(self, vkID):
        photo_dict = {}
        try:
            for photo in self.priv_api.photos.get(owner_id=vkID, album_id='profile', extended=1)['items']:
                print(photo)
                photo_dict[photo['sizes'][-1]['url']] = photo['likes']['count']
            return sorted(photo_dict, key=lambda x: x[1], reverse=True)[
                   :3]  # sorted list of photo by Likes, limited by to 3
            # print(self.priv_api.users.get(user_ids=vkID,)['first_name'])
        except:
            return []


if __name__ == '__main__':
    bd = BotDB()
    bd.create_tables()  # раскоментировать для инициализации базы
    vkbot = vkBOT(bd)
    vkbot.run()
    # vkbot.get_user_photos(vkID=64049236)
