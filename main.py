#---------------------------------------- ИМПОРТ БИБЛИОТЕК --------------------------------------------------------------------------------------------------------------------

from datetime import datetime
from transliterate import translit
from jinja2 import Environment, FileSystemLoader
import os, codecs, json, ipaddress, smtplib, configparser

from emailsendler import sendmail

#---------------------------------------- СЧИТЫВАНИЕ И ПАРСИНГ ДАННЫХ ИЗ БД /db/clients/*.json --------------------------------------------------------------------------------

def convert_file_to_list_of_json(path_to_file_vpn: str, attr_of_file_vpn:list):

    with codecs.open( path_to_file_vpn, "r", "utf_8_sig" ) as file_vpn:
        file_vpn_as_list = file_vpn.read().split('\n') # или читайте по строке
        file_vpn_as_list = list(filter(None, file_vpn_as_list)) # исключаем пустые строки
        file_vpn.close()
        list_of_json_from_file = list()

        for row in file_vpn_as_list:
            splited_row = row.split(',')
            if len(splited_row) == len(attr_of_file_vpn): 
                list_of_json_from_file.append(dict(zip(attr_of_file_vpn, splited_row)))
            else: 
                return f'Количество атрибутов *{len(attr_of_file_vpn)}* не соответствует количеству элементов в строке *{len(splited_row)}*'         
    return list_of_json_from_file

#---------------------------------------- ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ОПТИМАЛЬНОГО allocated_ips ИЗ ПУЛА АДРЕСОВ --------------------------------------------------------------------

def get_list_of_allocated_ips(path_to_db_clients: str, ip_range: str, gateway_ip):

    list_of_ip_range = list(ipaddress.ip_network(ip_range, False).hosts()) # находим список всех адресов пула
    list_of_db_filenames = os.listdir(path_to_db_clients) # находим названия всех файлов БД
    list_of_busy_ip = [gateway_ip] # инициализируем список занятых адресов с первым элементом - шлюзом

    for el in list_of_db_filenames:
        with open(f'{path_to_db_clients}/{el}', 'r', encoding='utf-8') as f: #открыли файл с данными
            obj = json.load(f) #загнали все, что получилось в переменную
            interface = ''.join(obj['allocated_ips']).partition('/')[0] # получили ip без маски
            list_of_busy_ip.append(ipaddress.ip_address(interface)) # пополняем список занятых ip адресов

    list_of_allocated_ips = list(set(list_of_ip_range) ^ set(list_of_busy_ip)) # получаем список всех свободных адресов 

    return list_of_allocated_ips # возвращаем свободные ip адреса

#---------------------------------------- ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ datetime.now() В НУЖНОМ ДЛЯ created_at, updated_at ФОРМАТЕ ----------------------------------------------------

def convert_datetime_now_to_formatted_datetime():
    now = datetime.now()
    formatted_datetime_to_json = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    formatted_datetime_to_conf = now.strftime("%Y-%m-%d %H:%M:%S.%f +0000 UTC")
    return formatted_datetime_to_json, formatted_datetime_to_conf

#---------------------------------------- ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ ID -----------------------------------------------------------------------------------------------------------

def get_translit_string(string: str):

    string.rstrip()
    translit_string = translit(string, language_code='ru', reversed=True).replace(" ", "_")
    chars_to_remove = [".", "'"]
    for char in chars_to_remove:
        translit_string = translit_string.replace(char, "")

    return translit_string

#---------------------------------------- ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ КЛЮЧЕЙ (private_key, public_key, preshared_key)  --------------------------------------------------------------

def generate_rsa_keys():

    list_rsa_keys = os.popen('umask 077 && wg genkey > prkey && cat prkey && wg pubkey < prkey; wg genpsk').readlines()
    list_rsa_keys = [row.rstrip() for row in list_rsa_keys]
    private_key = list_rsa_keys[0]
    public_key = list_rsa_keys[1]
    preshared_key = list_rsa_keys[2]
    return private_key, public_key, preshared_key

#---------------------------------------- ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ НОВОГО JSON ФАЙЛА  --------------------------------------------------------------------------------------------

def get_new_list_of_json(list_of_json_from_file, attr_of_db_client, list_of_allocated_ips, allowed_ip, for_what = None):

    new_list_of_json = list()
    formatted_datetime_to_json, formatted_datetime_to_conf = convert_datetime_now_to_formatted_datetime()
    print(list_of_json_from_file)

    for row in list_of_json_from_file: 
        el_of_new_list_json = dict()
        private_key, public_key, preshared_key = generate_rsa_keys()
        for el in attr_of_db_client:
            try:
                el_of_new_list_json[el] = row[el]
            except:

                if el == 'id':
                    idOfRow = get_translit_string(row['name']) + '_' + get_translit_string(row['email'])
                    el_of_new_list_json[el] = idOfRow

                elif el == 'private_key':
                    el_of_new_list_json[el] = private_key

                elif el == 'public_key':
                    el_of_new_list_json[el] = public_key

                elif el == 'preshared_key':
                    el_of_new_list_json[el] = preshared_key

                elif el == 'allocated_ips':
                    minAllocatedIp = min(list_of_allocated_ips)
                    el_of_new_list_json[el] = [format(ipaddress.IPv4Address(minAllocatedIp)) + '/32']
                    list_of_allocated_ips.remove(minAllocatedIp)

                elif el == 'allowed_ips':
                    el_of_new_list_json[el] = [allowed_ip]

                elif el == 'extra_allowed_ips':
                    el_of_new_list_json[el] = []

                elif el == 'use_server_dns':
                    el_of_new_list_json[el] = True

                elif el == 'enabled':
                    el_of_new_list_json[el] = True

                elif el == 'created_at' or el == 'updated_at':
                    el_of_new_list_json[el] =  formatted_datetime_to_json

                else:
                    el_of_new_list_json[el] = None
        
        if for_what == 'zip':
            el_of_new_list_json['number'] = row['number'].rstrip()

        new_list_of_json.append(el_of_new_list_json)

    return new_list_of_json

#---------------------------------------- ФУНКЦИЯ ДЛЯ ДОПОЛНЕНИЯ БАЗЫ КЛИЕНТОВ --------------------------------------------------------------------------------------------

def add_new_db_clients(path_to_db_clients, new_list_of_json):
    
    if not os.path.exists(path_to_db_clients):
        os.mkdir(path_to_db_clients)

    for row in new_list_of_json:
        new_json_file = json.dumps(row, indent=4)
        filename = row['id'] + '.json'
        if not os.path.exists(f'{path_to_db_clients}/{filename}'):
            with open(f'{path_to_db_clients}/{filename}', 'w+') as create_file:
                create_file.write(new_json_file)
                create_file.close()
        else:
            return True # Возвращаем True если такая конфа уже есть

#---------------------------------------- ФУНКЦИЯ ДЛЯ ДОПОЛНЕНИЯ КОФИГУРАЦИОННОГО ФАЙЛА (/etc/wireguard/)  -----------------------------------------------------------------

def add_to_conf_file(new_list_of_json, path_to_template, filename_template, path_to_conf, flag: bool):
    environment = Environment(loader=FileSystemLoader(path_to_template))
    template = environment.get_template(filename_template)
    formatted_datetime_to_json, formatted_datetime_to_conf = convert_datetime_now_to_formatted_datetime()
    new_users = list()

    if flag != True: # Если flag = True то конфигурация уже есть

        for new_user in new_list_of_json:
            content = template.render(
                new_user,
                AllowedIPs = ''.join(new_user["allocated_ips"]),
                datetimenow = formatted_datetime_to_conf
                )
            new_users.append(content)

        with open(path_to_conf, mode="a+", encoding="utf-8") as add_to_conf_file:
            for new_user in new_users:
                add_to_conf_file.seek(0, 2)
                add_to_conf_file.write('\n' + new_user + '\n')

#---------------------------------------- MAIN FUNCTION -----------------------------------------------------------------------------------------------------------------------

def main():

    config = configparser.ConfigParser()
    config.read('config.ini')
    main_conf = config['Wg']
    ip_conf = config['IpConf']
#---------------------------------------- ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ ------------------------------------------------------------------------------------------------------------
    
    path_to_db_clients = main_conf['PathDbClients'] # адрес базы клиентов (/db/clients/*.json)
    path_to_file = main_conf['PathToCsvUsers'] # адрес списка впн юзеров
    path_to_conf = main_conf['PathToConf'] # путь к csv файлу

    allowed_ip = ip_conf['AllowedIp']
    ip_range = ip_conf['IpRange'] # пул адресов
    ip_gateway = ipaddress.IPv4Address(ip_range.partition('/')[0])
    ip_range_prefix = (str(ipaddress.IPv4Network(ip_range, strict=False).prefixlen))

    path_to_templates = "./templates"
    filename_conf_template = "conf_template.txt"
    file_name_zip_template = "zip_template.txt"

#---------------------------------------- ЗАДАНИЕ АТРИБУТОВ ДЛЯ СОЗДАНИЯ СЛОВАРЯ ИЗ СПИСКА ВПН ЮЗЕРОВ И БД клиентов /db/clients/*.json ----------------------------------------

    # атрибуты списка впн юзеров
    attr_of_file_vpn = ['name', 'dep', 'spec', 'email', 'number']
    #атрибуты бд клиентов
    attr_of_db_client = ['id','private_key','public_key','preshared_key','name','email','allocated_ips','allowed_ips','extra_allowed_ips','use_server_dns','enabled','created_at','updated_at']

    list_of_json_from_file = convert_file_to_list_of_json(path_to_file, attr_of_file_vpn) # получаем массив словарей из файла csv ВПН юзеров типа {"title_rows_listVPN" : "VPNUserData"}
    print(list_of_json_from_file)
    list_of_allocated_ips = get_list_of_allocated_ips(path_to_db_clients, ip_range, ip_gateway) # свободные отсортированные ip адреса из пула
    new_list_of_json_to_zip = get_new_list_of_json(list_of_json_from_file, attr_of_db_client, list_of_allocated_ips, allowed_ip, 'zip') # получаем список json для zip
    new_list_of_json_to_db = get_new_list_of_json(list_of_json_from_file, attr_of_db_client, list_of_allocated_ips, allowed_ip) # получаем список json для /db/clients

    flag_to_conf = add_new_db_clients(path_to_db_clients, new_list_of_json_to_db)
    add_to_conf_file(new_list_of_json_to_db, path_to_templates, filename_conf_template, path_to_conf, flag_to_conf)

    sendmail.send_mail_message(new_list_of_json_to_zip)

if __name__ == '__main__':
    main()



