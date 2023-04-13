#---------------------------------------- ИМПОРТ БИБЛИОТЕК --------------------------------------------------------------------------------------------------------------------

from datetime import datetime
from transliterate import translit
import os, codecs, json, ipaddress, smtplib

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

def get_AllocatedIps(pathToDbClients, ipRange, gateAwayIp):

    listOfIpRange = list(ipaddress.ip_network(ipRange, False).hosts()) # находим список всех адресов пула
    listOfFiles = os.listdir(pathToDbClients) # находим названия всех файлов БД
    listOfBusyAllocatedIps = [gateAwayIp]

    for el in listOfFiles:
        with open(f'./clients/{el}', 'r', encoding='utf-8') as f: #открыли файл с данными
            obj = json.load(f) #загнали все, что получилось в переменную
            interface = ''.join(obj['allocated_ips']).partition('/')[0] # получили ip без маски
            listOfBusyAllocatedIps.append(ipaddress.ip_address(interface)) # пополняем список занятых ip адресов

    listOfallowableIps = list(set(listOfIpRange) ^ set(listOfBusyAllocatedIps)) # получаем список всех свободных адресов 

    return listOfallowableIps # возвращаем минимальный свободный ip адрес

#---------------------------------------- ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ datetime.now() В НУЖНОМ ДЛЯ created_at, updated_at ФОРМАТЕ ----------------------------------------------------

def get_dateTimeNow():
    now = datetime.now()
    nowParse = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return nowParse

#---------------------------------------- ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ ID ---------------------------------------------------------------------------------------------------------

def get_translitString(str):

    strOut = translit(str, language_code='ru', reversed=True).replace(" ", "_")
    charsToRemove = [".", "'"]
    for char in charsToRemove:
        strOut = strOut.replace(char, "")

    return strOut

#---------------------------------------- ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ КЛЮЧЕЙ (private_key, public_key, preshared_key)  --------------------------------------------------------------

def generateKeys():

    list_keys = os.popen('umask 077 && wg genkey > prkey && cat prkey && wg pubkey < prkey; wg genpsk').readlines()
    list_keys = [row.rstrip() for row in list_keys]
    privateKey = list_keys[0]
    public_key = list_keys[1]
    preshared_key = list_keys[2]
    privateKey, public_key, preshared_key

#---------------------------------------- ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ НОВОГО JSON ФАЙЛА  --------------------------------------------------------------------------------------------

def get_newJSONconf(massOfVPNdicts, title_rows_dbClients, nowParse, listAllocatedIp, allowedIp, prefixOfIpRange):
 
    massOfWgConf = []

    for row in massOfVPNdicts: 
        elOfWgConf = {}
        privateKey, public_key, preshared_key = generateKeys()
        for el in title_rows_dbClients:
            try:
                elOfWgConf[el] = get_translitString(row[el]) 
            except:

                if el == 'id':
                    idOfRow = get_translitString(row['name']) + '_' + get_translitString(row['email'])
                    elOfWgConf[el] = idOfRow

                elif el == 'private_key':
                    elOfWgConf[el] = privateKey

                elif el == 'public_key':
                    elOfWgConf[el] = public_key

                elif el == 'preshared_key':
                    elOfWgConf[el] = preshared_key

                elif el == 'allocated_ips':
                    minAllocatedIp = min(listAllocatedIp)
                    elOfWgConf[el] = [format(ipaddress.IPv4Address(minAllocatedIp)) + '/' + prefixOfIpRange]
                    listAllocatedIp.remove(minAllocatedIp)

                elif el == 'allowed_ips':
                    elOfWgConf[el] = [allowedIp]

                elif el == 'extra_allowed_ips':
                    elOfWgConf[el] = []

                elif el == 'use_server_dns':
                    elOfWgConf[el] = True

                elif el == 'enabled':
                    elOfWgConf[el] = True

                elif el == 'created_at' or el == 'updated_at':
                    elOfWgConf[el] =  nowParse

                else:
                    elOfWgConf[el] = None

        massOfWgConf.append(elOfWgConf)

    return massOfWgConf

#---------------------------------------- ФУНКЦИЯ ДЛЯ ЗАПИСИ НОВОГО JSON ФАЙЛА  --------------------------------------------------------------------------------------------

def set_NewJSONconf(nameOfNewPathDB, massOfWgConf):
    
    if not os.path.exists(nameOfNewPathDB):
        os.mkdir(nameOfNewPathDB)
    for row in massOfWgConf:
        nameForGenId = row['name']#get_translitString(row['name'])
        emailForGenId = row['email']#get_translitString(row['email'])
        jsonFile = json.dumps(row, indent=4)
        genId = nameForGenId + '_' + emailForGenId
        with open(f'{nameOfNewPathDB}/{genId}.json', 'w+') as createFile:
            createFile.write(jsonFile)
            createFile.close()

#---------------------------------------- ФУНКЦИЯ ДЛЯ ОТПРАВКИ СООБЩЕНИЯ ПО ПОЧТЕ  --------------------------------------------------------------------------------------------

def sendMessageToSMTPServer(addrOfSMTPServer, portOfSMTPServer, login, passwd):

    smtpObj = smtplib.SMTP(addrOfSMTPServer, portOfSMTPServer)
    smtpObj.starttls()
    smtpObj.login(login, passwd)

#---------------------------------------- MAIN FUNCTION -----------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

#---------------------------------------- ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ ------------------------------------------------------------------------------------------------------------

    pathToDbClients = './clients' # адрес базы клиентов (/db/clients/*.json)
    pathToListVPN = 'listVPN.csv' # адрес списка впн юзеров
    nameOfNewPathDB = 'newClient'

    allowedIp = '192.168.0.0/21'
    ipRange = '10.66.66.1/24' # пул адресов

    gateAwayIp = ipaddress.IPv4Address(ipRange.partition('/')[0])
    prefixOfIpRange = (str(ipaddress.IPv4Network(ipRange, strict=False).prefixlen))



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
    AllocatedIps = get_AllocatedIps(pathToDbClients, ipRange, gateAwayIp) # свободные отсортированные ip адреса из пула
    dateTimeNow = get_dateTimeNow() # текущая дата в нужном формате
    newJSONconf = get_newJSONconf(massOfVPNdicts, title_rows_dbClients, dateTimeNow, AllocatedIps, allowedIp, prefixOfIpRange) # массив новых JSON файлов


    set_NewJSONconf(nameOfNewPathDB, newJSONconf)

