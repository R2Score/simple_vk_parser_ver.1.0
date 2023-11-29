# -*- coding: utf-8 -*-

"""
    Этот простой скрипт заливает фотографии профиля VK на Яндекс.Диск
без предварительной загрузки на компьютер. Спроектирован следуя процедурной методологии,
обрабатывает ряд базовых исключений.
    В дальнейшем будет доработан для безопасного вызова tokens
из переменных окружения.  

    1.  Перед запуском пройдите по ссылкам в файле my_tokens.py,
        получив tokens вставьте их вместо ссылок в ''.
    2.  Запустите скрипт и следуйте инструциям в консоли.

"""

import requests
import json
from tqdm import tqdm
from my_tokens import TOKEN_VK, TOKEN_YD


def main_input():
    # =============================================================================
    # '''Блок запроса значений для работы скрипта'''
    # =============================================================================
    input_for_vk_id = input('\t1. Введите id пользователя: ') or '1'
    if input_for_vk_id.isdigit():
        vk_id = int(input_for_vk_id)
        if vk_id <= 0:
            print('\tid не может быть 0!!!')
        else:
            input_for_vk_count = input('\t2. Укажите кол-во фото для сохранения на ЯД: ') or '5'
            if input_for_vk_count.isdigit():
                vk_count = int(input_for_vk_count)
                if vk_count <= 0:
                    print('\tКол-во фото не может быть 0!!!')
                else:
                    input_for_yd_folder = input('\t3. Введите название новой папки \
                                  \n\tили укажите путь до нужной через "/".\
                                  \n\tВы можете создать папку в имеющейся: ') or 'simple_vk_parser'
                    yd_folder = input_for_yd_folder
                    if yd_folder is not '':
                        return vk_pics_parser(vk_id, vk_count, yd_folder)
                    else:
                        print('\tУкажите название папки!!!')      
            else:
                 print('\tУкажите цифры в поле фото')    
    else:
        print('\tУкажите цифры в поле id')
               
def vk_pics_parser(vk_id, vk_count, yd_folder):
    # =============================================================================
    # '''Блок запроса фотографий из профиля VK'''
    # =============================================================================
    URL_VK_PHOTOS_GET = 'https://api.vk.com/method/photos.get'
    params_vk = {'owner_id': vk_id,
                 'access_token': TOKEN_VK,
                 'v': '5.131',
                 'album_id': 'profile',
                 'count': vk_count,
                 'extended': '1',
                 'photo_sizes': '1'}

    try:
        response_vk = requests.get(URL_VK_PHOTOS_GET, params=params_vk)
        albums_dict_list = response_vk.json()['response']['items']
    
        print(f'\tПолучен ответ сервера - {response_vk.status_code} ок!')
        return yd_create_folder(yd_folder, albums_dict_list)
        
    except KeyError:
        closed = 'Профиль закрыт!!!'
        deleted = 'Профиль деактивирован!!!'
        access_denied = 'Вас заблокировали!!!'
 
        if response_vk.json()['error']['error_code'] == 30:
            print(
              f'\t{closed} код {response_vk.json()["error"]["error_code"]}!!!')
        if response_vk.json()['error']['error_code'] == 15:
            print(
             f'\t{deleted} код {response_vk.json()["error"]["error_code"]}!!!')
        if response_vk.json()['error']['error_msg'] == 'Access denied':
            print(
             f'\t{access_denied} Cообщение сервера:{response_vk.json()["error"]["error_msg"]}!!!')
            
def yd_create_folder(yd_folder, albums_dict_list):
    # =============================================================================
    # '''Блок создания папки на ЯД'''
    # =============================================================================
    URL_YD_CREATE_FOLDER_PUT =\
        'https://cloud-api.yandex.net/v1/disk/resources'
    headers_yd = {'Content-Type': 'application/json',
                  'Accept': 'application/json',
                  'Authorization': f'OAuth {TOKEN_YD}'}

    path = yd_folder
    response_yd = requests.put(f'{URL_YD_CREATE_FOLDER_PUT}?path={path}',
                               headers=headers_yd)
    if response_yd.status_code == 409:
        print(f'\tСнимки будут записаны в существующую папку: {yd_folder} - {response_yd.status_code} ок!')
    elif response_yd.status_code == 201:
        print(f'\tПапка {yd_folder} создана - {response_yd.status_code} ок!')
    return loop_pics_url_uploader(path, albums_dict_list)

def loop_pics_url_uploader(path, albums_dict_list):
    # =============================================================================
    # '''Блок цикла выборки фото c передачей загрузчику ЯД по ссылке'''
    # =============================================================================
    pic_dicts_list = []
    for pics in tqdm(albums_dict_list, ncols=80, ascii=True,
                     desc=f'\tПрогресс выборки/записи'):
        pics_size = (pics['sizes'][-1])
        pics_url = (pics_size['url'])
        pics_type = (pics_size['type'])
        pics_name = []

        if pics['likes']['count'] == 0:
            pics_name = pics['date']
        if pics['likes']['count'] > 0:
            pics_name = pics['likes']['count']

        pic_dicts_list.append({'Название фото': pics_name,
                               'Размер фото': pics_type})

        URL_YD_UPLOAD_POST =\
            'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers_yd = {'Content-Type': 'application/json',
                      'Accept': 'application/json',
                      'Authorization': f'OAuth {TOKEN_YD}'}

        params_yd = {'url': pics_url,
                     'path': f'/{path}/{pics_name}.jpg',
                     'overwrite': 'true'}

        response = requests.post(URL_YD_UPLOAD_POST,
                                 params=params_yd,
                                 headers=headers_yd)
    print(f'\n\tОтвет сервера {response.status_code} - загружено!')
    return json_pics_info_creater(pic_dicts_list)

def json_pics_info_creater(pic_dicts_list):
    # =============================================================================
    # '''Блок запись/вывод json c инфо о фото'''
    # =============================================================================
    file = input('Укажите название файла отчёта: ') or 'Отчёт'
    with open(f'{file}.json', 'w') as outfile:
        json.dump(pic_dicts_list, outfile)

    with open(f'{file}.json') as file:
        pics = json.load(file)
        print(f'\n\t{pics}')


if __name__ == "__main__": 
    main_input()