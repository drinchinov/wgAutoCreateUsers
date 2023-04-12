#---------------------------------------- ИМПОРТ БИБЛИОТЕК --------------------------------------------------------------------------------------------------------------------

from datetime import datetime
from transliterate import translit
import os, codecs, json, ipaddress, uuid

#---------------------------------------- СЧИТЫВАНИЕ И ПАРСИНГ ДАННЫХ ИЗ БД /db/clients/*.json --------------------------------------------------------------------------------

def get_massOfVPNdicts(pathToListVPN, title_rows_listVPN):
    with codecs.open( pathToListVPN, "r", "utf_8_sig" ) as listVPN_input:

        listVPN_output = listVPN_input.read().split('\n') # или читайте по строке
        listVPN_input.close()
        massOfVPNdicts = []

        for row in listVPN_output:
            strVPN = row.split(',')
            if len(strVPN) == 5:
                massOfVPNdicts.append(dict(zip(title_rows_listVPN, strVPN)))
    return massOfVPNdicts

#---------------------------------------- ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ОПТИМАЛЬНОГО allocated_ips ИЗ ПУЛА АДРЕСОВ --------------------------------------------------------------------

def get_minAllocatedIp(pathToDbClients, ipRange):

    listOfIpRange = list(ipaddress.ip_network(ipRange, False).hosts()) # находим список всех адресов пула
    listOfFiles = os.listdir(pathToDbClients) # находим названия всех файлов БД
    listOfBusyAllocatedIps = []

    for el in listOfFiles:
        with open(f'./clients/{el}', 'r', encoding='utf-8') as f: #открыли файл с данными
            obj = json.load(f) #загнали все, что получилось в переменную
            interface = ''.join(obj['allocated_ips']).partition('/')[0] # получили ip без маски
            listOfBusyAllocatedIps.append(ipaddress.ip_address(interface)) # пополняем список занятых ip адресов

    listOfallowableIps = list(set(listOfIpRange) ^ set(listOfBusyAllocatedIps)) # получаем список всех свободных адресов 
    minOFlistOfallowableIps = min(listOfallowableIps)
    return format(ipaddress.IPv4Address(minOFlistOfallowableIps)) # возвращаем минимальный свободный ip адрес

#---------------------------------------- ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ datetime.now() В НУЖНОМ ДЛЯ created_at, updated_at ФОРМАТЕ ----------------------------------------------------

def get_dateTimeNow():
    now = datetime.now()
    nowParse = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return nowParse

#---------------------------------------- ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ НОВОГО JSON ФАЙЛА  --------------------------------------------------------------------------------------------

def get_newJSONconf(massOfVPNdicts, title_rows_dbClients, nowParse, minAllocatedeIp, allowedIp):

    elOfWgConf = {}
    massOfWgConf = []

    for row in massOfVPNdicts:
        for el in title_rows_dbClients:
            try:
                elOfWgConf[el] = translit(row[el], language_code='ru', reversed=True)
            except:
                if el == 'id':
                    elOfWgConf[el] = get_idForJSONFile(row['name'], row['email'])
                elif el == 'created_at' or el == 'updated_at':
                    elOfWgConf[el] =  nowParse
                elif el == 'allocated_ips':
                    elOfWgConf[el] = [minAllocatedeIp]
                elif el == 'allowed_ips':
                    elOfWgConf[el] = [allowedIp]
                else:
                    elOfWgConf[el] = None
        massOfWgConf.append(elOfWgConf)

    return massOfWgConf

#---------------------------------------- ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ ID ---------------------------------------------------------------------------------------------------------

def get_idForJSONFile(name, email):
    return name.replace(' ', '_') + email.replace(' ', '_')

#---------------------------------------- ФУНКЦИЯ ДЛЯ ЗАПИСИ НОВОГО JSON ФАЙЛА  --------------------------------------------------------------------------------------------

def set_NewJSONconf(massOfWgConf):

    for row in massOfWgConf:
        jsonFile = json.dumps(row, indent=4)
        genId = get_idForJSONFile(row['name'], row['email'])
        with open(f'{genId}.json', 'w+') as createFile:
            createFile.write(jsonFile)
            createFile.close()

#---------------------------------------- MAIN FUNCTION -----------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

#---------------------------------------- ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ ------------------------------------------------------------------------------------------------------------

    pathToDbClients = './clients' # адрес базы клиентов (/db/clients/*.json)
    pathToListVPN = 'listVPN.csv' # адрес списка впн юзеров

    allowedIp = '192.168.0.0/21'
    ipRange = '10.66.66.1/24' # пул адресов

#---------------------------------------- ЗАДАНИЕ АТРИБУТОВ ДЛЯ СОЗДАНИЯ СЛОВАРЯ ИЗ СПИСКА ВПН ЮЗЕРОВ И БД клиентов /db/clients/*.json ----------------------------------------

    # атрибуты списка впн юзеров
    title_rows_listVPN = [
                            'name',
                            'dep',
                            'spec',
                            'email',
                            'number'
                        ]

    #атрибуты бд клиентов
    title_rows_dbClients = [
                            'id',
                            'private_key',
                            'public_key',
                            'preshared_key',
                            'name',
                            'email',
                            'allocated_ips',
                            'allowed_ips',
                            'extra_allowed_ips',
                            'use_server_dns',
                            'enabled',
                            'created_at',
                            'updated_at'
                        ]


    massOfVPNdicts = get_massOfVPNdicts(pathToListVPN, title_rows_listVPN) # получаем массив словарей из списка ВПН юзеров типа {"title_rows_listVPN" : "VPNUserData"}
    minAllocatedIp = get_minAllocatedIp(pathToDbClients, ipRange) # минимальный свободный ip адрес из пула
    dateTimeNow = get_dateTimeNow() # текущая дата в нужном формате
    newJSONconf = get_newJSONconf(massOfVPNdicts, title_rows_dbClients, dateTimeNow, minAllocatedIp, allowedIp) # массив новых JSON файлов

    set_NewJSONconf(newJSONconf)

