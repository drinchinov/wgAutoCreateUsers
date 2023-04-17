import os, ipaddress, json
from transliterate import translit
from datetime import datetime

#---------------------------------------- ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ КЛЮЧЕЙ (private_key, public_key, preshared_key)  --------------------------------------------------------------

def get_rsa_keys():
    list_keys = os.popen('umask 077 && wg genkey > prkey && cat prkey && wg pubkey < prkey; wg genpsk').readlines()
    list_keys = [row.rstrip() for row in list_keys]
    private_key = list_keys[0]
    public_key = list_keys[1]
    preshared_key = list_keys[2]

    return private_key, public_key, preshared_key

#---------------------------------------- ФУНКЦИЯ ДЛЯ ТРАНСЛИТЕРАЦИИ СТРОК-----------------------------------------------------------------------------------------------------

def get_translit_string(string: str):

    translit_string = translit(string, language_code='ru', reversed=True).replace(" ", "_")
    chars_to_remove = [".", "'"]
    for char in chars_to_remove:
        translit_string = translit_string.replace(char, "")

    return translit_string

#---------------------------------------- ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ datetime.now() В НУЖНОМ ДЛЯ created_at, updated_at ФОРМАТЕ -----------------------------------------------------

def get_formatted_datetime_now():
    now = datetime.now()
    now_to_json = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    now_to_conf = now.strftime("%Y-%m-%d %H:%M:%S.%f +0000 UTC")
    return now_to_json, now_to_conf

#---------------------------------------- ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ОПТИМАЛЬНОГО allocated_ips ИЗ ПУЛА АДРЕСОВ --------------------------------------------------------------------

def get_list_of_allowable_ips(path_to_db_clients: str, ip_range: str, gateway_ip: str):

    list_of_ip_range = list(ipaddress.ip_network(ip_range, False).hosts()) # находим список всех адресов пула
    list_of_db_filenames = os.listdir(path_to_db_clients) # находим названия всех файлов БД
    list_of_busy_allocated_ips = [gateway_ip] # создаем список и инициализируем первый элемент - шлюз

    for el in list_of_db_filenames:
        with open(f'{path_to_db_clients}/{el}', 'r', encoding='utf-8') as f: #открыли файл с данными
            obj = json.load(f) #загнали все, что получилось в переменную
            interface = ''.join(obj['allocated_ips']).partition('/')[0] # получили ip без маски
            list_of_busy_allocated_ips.append(ipaddress.ip_address(interface)) # пополняем список занятых ip адресов

    list_of_allowable_ips = list(set(list_of_ip_range) ^ set(list_of_busy_allocated_ips)) # получаем список всех свободных адресов 

    return list_of_allowable_ips # возвращаем все свободные ip адрес