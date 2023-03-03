import vk_api
from vk_access_token import access_token

vk = vk_api.VkApi(token=access_token)
session_api = vk.get_api()

SEX = 1
AGE_FROM = 18
AGE_TO = 40
CITY = 1

params = {'count': 1000,
          'city': CITY,
          'sex': SEX,
          'age_from': AGE_FROM,
          'age_to': AGE_TO,
          'fields': 'can_write_private_message',
          'has_photo': 1}

users = session_api.users.search(**params)
# print(users)
avatar_links = {}
for i in users['items']:
    # print(i['is_closed'])
    if i['is_closed'] == False and i['can_write_private_message'] == 1:
        print(i['id'], i['last_name'], i['first_name'])
        photo = session_api.photos.get(owner_id=i['id'], album_id='profile', count=3, photo_sizes='x', extended=1)
        for y in photo['items']:
            if y['likes']['count'] in avatar_links.keys():
                avatar_links.update({y['likes']['count'] + y['date']: y['sizes'][-1]})
            else:
                avatar_links.update({y['likes']['count']: y['sizes'][-1]})
    else:
        pass

print(avatar_links)


