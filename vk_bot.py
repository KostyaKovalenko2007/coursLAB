import os
from random import randrange
import vk_api
import json
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor, VkKeyboardButton
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
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
        # self.longpoll = VkLongPoll(self.session)
        self.longpoll = VkBotLongPoll(self.session, group_id=GROUP_ID)
        self.db: BotDB = db
        self.vk = self.session.get_api()
        self.api = self.session.get_api()
        # self.priv_api = vk_api.VkApi(token=getenv('priv_token')).get_api()
        self.priv_api = vk_api.VkApi(token=USER_TOKEN).get_api()
        # self.upload = vk_api.VkUpload(self.session)
        self.vk_upload = vk_api.VkApi(token=USER_TOKEN)
        self.upload = VkUpload(self.vk_upload)

        self.keyb_main = VkKeyboard()
        self.keyb_main.add_callback_button(label='Поиск', color='primary', payload={"type": "search"})
        self.keyb_main.add_callback_button(label='Настройки', color='primary', payload={"type": "settings"})

        self.keyb_first_search = VkKeyboard()
        self.keyb_first_search.add_callback_button(label='Показать', color='positive', payload={"type": "first_show"})
        self.keyb_first_search.add_callback_button(label='Избранное', color='primary', payload={"type": "look_best"})
        self.keyb_first_search.add_callback_button(label='Назад', color='primary', payload={"type": "back"})

        self.keyb_search = VkKeyboard()
        self.keyb_search.add_callback_button(label='Следующее', color='positive', payload={"type": "next"})
        self.keyb_search.add_callback_button(label='Избранное', color='primary', payload={"type": "look_best"})
        self.keyb_search.add_callback_button(label='Назад', color='primary', payload={"type": "back"})

        self.keyb_like = VkKeyboard(inline=True)
        self.keyb_like.add_callback_button(label='В избранное', color='positive', payload={"type": "like"})
        self.keyb_like.add_callback_button(label='Не показывать', color='negative', payload={"type": "disslike"})

        self.search_settings = {}
        self.search_settings_status = 0

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



    def sendMessage(self, event, message, keyboard=None):
        post = {'user_id': event.obj.message['from_id'],
                'random_id': randrange(10 ** 7),
                'peer_id': event.obj.message['from_id'],
                'message': message}

        if keyboard:
            post["keyboard"] = keyboard.get_keyboard()

        self.session.method('messages.send', post)


    def write_bot_msg(self, event, message, keyboard=None):
        post = {'user_id': event.object.user_id,
                'random_id': randrange(10 ** 7),
                'peer_id': event.object.peer_id,
                'message': message}
        if keyboard:
            post["keyboard"] = keyboard.get_keyboard()
        self.session.method('messages.send', post)


    # Отправка VK ответа, что видим, что кнопка нажата
    def sendMessageEventAnswer(self, event):
        post = {'event_id': event.object.event_id,
                'user_id': event.object.user_id,
                'peer_id': event.object.peer_id,
                'conversation_message_id': event.obj.conversation_message_id}
        return self.session.method('messages.sendMessageEventAnswer', post)


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



        params = {'city': creteria['city'].get('id'),
                  'sex': creteria['sex'],
                  'fields': 'can_write_private_message',
                  'has_photo': 1}

        if self.search_settings.get('count') != None:
            params['count'] = self.search_settings['count']
        else:
            params['count'] = 10

        if self.search_settings.get('age_from') != None:
            params['age_from'] = self.search_settings['age_from']
        else:
            params['age_from'] = 18

        if self.search_settings.get('age_to') != None:
            params['age_to'] = self.search_settings['age_to']
        else:
            params['age_from'] = 40


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

    def get_like_profiles(self, ClientID):
        # возвращает следующий профиль из поисковых результатов
        return self.db.get_like_profiles(client=self.db.get_client_by_vkID(vkID=ClientID))

    def set_like_dislike(self, clientID, like=False):
        client = self.db.get_client_by_vkID(vkID=clientID)
        self.db.set_like(client=client,like=like)
        pass

    def run(self):
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.from_user:
                    new_message = event.message['text']
                    if new_message == 'start':
                        self.sendMessage(event, 'Привет! Управление ботом производится через кнопки', self.keyb_main)
                    elif '?' in new_message:
                        self.sendMessage(event, 'Я не очень умный бот, спроси лучше у Яндекса')
                    else:
                        if self.search_settings_status == 1:
                            if new_message.isdigit():
                                self.search_settings['count'] = int(new_message)
                                self.search_settings_status = 2
                                self.sendMessage(event, 'Введите начальный возраст поиска')
                            else:
                                self.sendMessage(event, 'Введите число')
                        elif self.search_settings_status == 2:
                            if new_message.isdigit():
                                self.search_settings['age_from'] = int(new_message)
                                self.search_settings_status = 3
                                self.sendMessage(event, 'Введите конечный возраст поиска')
                                print(self.search_settings)
                            else:
                                self.sendMessage(event, 'Введите число')
                        elif self.search_settings_status == 3:
                            if new_message.isdigit():
                                self.search_settings['age_to'] = int(new_message)
                                self.search_settings_status = 0
                                self.sendMessage(event, 'Параметры поиска получены')
                                print(self.search_settings)
                            else:
                                self.sendMessage(event, 'Введите число')
                        else:
                            self.sendMessage(event, 'Для начала работы с ботом введите команду start')
            elif event.type == VkBotEventType.MESSAGE_EVENT:
                if command := event.object.payload.get('type'):
                    print(command)
                    user_id = event.object.user_id
                    self.sendMessageEventAnswer(event)
                    if command == "search":
                        self.register_client_profile(user_id=user_id)
                        info = self.db.get_client_criterias(vkID=str(user_id))
                        self.write_bot_msg(event, "Выполняем поиск...", None)
                        if len(self.search_settings) == 0:
                            self.write_bot_msg(event,
                                           "Ваши поисковые критерии:\n" \
                                           f"Город: {info['city'].get('title')}\n" \
                                           f"Пол: {self.sex[info.get('sex')]}\n" \
                                           f"Возраст: {info.get('bdate')}", None)

                        self.search_by_client_criteria(Client_id=user_id)
                        self.write_bot_msg(event, "Поиск произведен", self.keyb_first_search)
                    elif command == "first_show":
                        self.write_bot_msg(event, "Понравившиеся профили можно добавлять в избранное", self.keyb_search)
                        self.send_profile(user_id, self.get_next_in_searchResults(ClientID=user_id), self.keyb_like)
                    elif command == "next":
                        self.send_profile(user_id, self.get_next_in_searchResults(ClientID=user_id), self.keyb_like)
                    elif command == "like":
                        self.set_like_dislike(clientID=user_id, like=True)
                    elif command == "disslike":
                        self.set_like_dislike(clientID=user_id, like=False)
                    elif command == "back":
                        self.write_bot_msg(event, "Возврат в основное меню", self.keyb_main)
                    elif command == "look_best":
                        profiles = self.get_like_profiles(ClientID=user_id).all()
                        if len(profiles):
                            self.write_bot_msg(event, "Понравившиеся профили:")
                            for profile in profiles:
                                self.write_bot_msg(event, f'{profile.fio} https://vk.com/id{profile.vkID}')
                        else:
                            self.write_bot_msg(event, "В избранном никого нет")
                    elif command == "settings":
                        self.search_settings_status = 1
                        self.write_bot_msg(event, 'Задайте количество профилей для просмотра:')




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
