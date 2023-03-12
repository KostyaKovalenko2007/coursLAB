import os
from random import randrange
import vk_api
import json
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor, VkKeyboardButton
from db import Client, SearchResult, Favorite, BotDB
from os import getenv
from settings import GROUP_ID, GROUP_TOKEN, USER_TOKEN, API_VERSION
from vk_api import VkUpload
import requests



class vkBOT():
    session = None
    api = None
    db: BotDB = None
    sex = {1: 'Женский', 2: 'Мужской'}
    priv_api = None
    vk_upload = None

    def __init__(self, db: BotDB):
        # self.session = vk_api.VkApi(token=getenv('token'))
        self.session = vk_api.VkApi(token=GROUP_TOKEN)
        self.longpoll = VkLongPoll(self.session)
        self.db: BotDB = db
        self.vk = self.session.get_api()
        self.api = self.session.get_api()
        # self.priv_api = vk_api.VkApi(token=getenv('priv_token')).get_api()
        self.priv_api = vk_api.VkApi(token=USER_TOKEN).get_api()
        # self.upload = vk_api.VkUpload(self.session)
        self.vk_upload = vk_api.VkApi(token=USER_TOKEN)
        self.upload = VkUpload(self.vk_upload)

    def send_profile(self,user_id,profile:dict,keyboard):
        # print(profile.get('fio'),profile.get('img1'))

        fotos = []
        if profile.get('img1'):
            fotos.append(profile.get('img1'))
        if profile.get('img2'):
            fotos.append(profile.get('img2'))
        if profile.get('img3'):
            fotos.append(profile.get('img3'))
        message = f"{profile.get('fio')} {profile.get('profile')}"

        attachments = []
        session = requests.Session()
        for foto in fotos:
            image = session.get(foto, stream=True)
            photo = self.upload.photo_messages(photos=image.raw)[0]
            attachments.append('photo{}_{}_{}'.format(photo['owner_id'], photo['id'], photo['access_key']))
        post = {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7), 'attachment': ','.join(attachments)}
        if keyboard:
            post["keyboard"] = keyboard.get_keyboard()
        self.session.method('messages.send', post)
        #pic1 = self.upload.photo_messages(profile.get('img1'))
        # pic1 = self.upload.photo_messages("/Users/air/Downloads/VzazMS50ug4.jpeg", peer_id=64049236)
        # print(pic1)

    def write_msg(self, user_id, message, keyboard=None):
        post = {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7)}
        if keyboard:
            post["keyboard"] = keyboard.get_keyboard()
        self.session.method('messages.send', post)

    def register_client_profile(self, user_id):
        info = self.api.users.get(user_ids=user_id, fields='city, sex, bdate')[0]
        if info.get('sex') == 1:
            info['sex'] = 2
        elif info.get('sex') == 2:
            info['sex'] = 1

        result, msg = self.db.create_client(vkID=user_id, creteria=json.dumps(info))
        print(msg)
        return result

    def search_by_client_criteria(self, Client_id):
        # делает выборку/поиск из VK, результат кладет в базу

        creteria = self.db.get_client_criterias(vkID=Client_id)

        params = {'count': 20,
                  'city': creteria['city'].get('id'),
                  'sex': creteria['sex'],
                  # 'age_from': AGE_FROM, #TODO надо подять как обрабатывать возраст
                  # 'age_to': AGE_TO,
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

        pass

    def get_next_in_searchResults(self, ClientID):
        # возвращает следующий профиль из поисковых результатов
        return self.db.get_next_profile(client=self.db.get_client_by_vkID(vkID=ClientID))


    def set_like_dislike(self, clientID, like=False):
        client = self.db.get_client_by_vkID(vkID=clientID)
        self.db.set_like(client=client,like=like)
        pass

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
                        self.send_profile(event.user_id, self.get_next_in_searchResults(ClientID=event.user_id), keyboard)
                    elif request == "Регистрация":
                        self.register_client_profile(user_id=event.user_id)
                        info = self.db.get_client_criterias(vkID=str(event.user_id))
                        self.write_msg(event.user_id, "Вас зарегистрировали", None)
                        self.write_msg(event.user_id,
                                       "Ваши поисковые критерии:\n" \
                                       f"Город: {info['city'].get('title')}\n" \
                                       f"Пол: {self.sex[info.get('sex')]}\n" \
                                       f"Возраст: {info.get('bdate')}", None)
                        keyboard = VkKeyboard()
                        keyboard.add_button("Введите город", VkKeyboardColor.POSITIVE)
                        keyboard.add_button("Введите возраст", VkKeyboardColor.POSITIVE)
                        # self.write_msg(event.user_id, "button", keyboard)
                    elif request == "Следующее":
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button("Нравится", VkKeyboardColor.POSITIVE)
                        keyboard.add_button("Не нравится", VkKeyboardColor.NEGATIVE)
                        keyboard.add_button("Следующее", VkKeyboardColor.PRIMARY)
                        self.send_profile(event.user_id, self.get_next_in_searchResults(ClientID=event.user_id), keyboard)
                    elif request == "Нравится":
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button("Нравится", VkKeyboardColor.POSITIVE)
                        keyboard.add_button("Не нравится", VkKeyboardColor.NEGATIVE)
                        keyboard.add_button("Следующее", VkKeyboardColor.PRIMARY)
                        self.set_like_dislike(clientID=event.user_id,like=True )
                    elif request == "Не нравится":
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button("Нравится", VkKeyboardColor.POSITIVE)
                        keyboard.add_button("Не нравится", VkKeyboardColor.NEGATIVE)
                        keyboard.add_button("Следующее", VkKeyboardColor.PRIMARY)
                        self.set_like_dislike(clientID=event.user_id,like=False )
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
    # bd.create_tables() # раскоментировать для инициализации базы
    vkbot = vkBOT(bd)
    vkbot.run()
    #vkbot.get_user_photos(vkID=64049236)
