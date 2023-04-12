from datetime import datetime, date, time
from transliterate import translit
import csv
import codecs
import json
import uuid

import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


pathOfListVPN = 'listVPN_test.csv'

title_rows_listVPN = [
                        'name',
                        'dep',
                        'spec',
                        'email',
                        'number'
                    ]
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

#Иванов Иван Иванович,Отдел разработки,специалист по PLSQL,coolsqlproger@mail.ru,87777777777

with codecs.open( pathOfListVPN, "r", "utf_8_sig" ) as listVPN_input:

    listVPN_output = listVPN_input.read().split('\n') # или читайте по строке
    listVPN_input.close()
    massOfVPNdicts = []

    for row in listVPN_output:
        strVPN = row.split(',')
        if len(strVPN) == 5:
            massOfVPNdicts.append(dict(zip(title_rows_listVPN, strVPN)))
        

massOfWgConf = []
elOfWgConf = {}
now = datetime.now()
nowParse = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

for row in massOfVPNdicts:
#    for k, v in row.items():
    for row1 in title_rows_dbClients:
        try:
            elOfWgConf[row1] = translit(row[row1], language_code='ru', reversed=True)
            #print(row1, row[row1])
        except:
            if row1 == 'created_at' or row1 == 'updated_at':
               elOfWgConf[row1] =  nowParse
            elif 'ips' in row1:
                elOfWgConf[row1] = []
            else:
                elOfWgConf[row1] = None
            #print(row1, None)
    massOfWgConf.append(elOfWgConf)


for row in massOfWgConf:
    jsonFile = json.dumps(row, indent=4)
    with open(f'{uuid.uuid4()}.json', 'w+') as createFile:
        createFile.write(jsonFile)
        createFile.close()
print('---------------------------------')



'''try:
                print(row[row1])
                elOfWgConf = row.fromkeys(row1, v)
                massOfWgConf.append(elOfWgConf)
            except:
                elOfWgConf = row.fromkeys(row1, None)
                massOfWgConf.append(elOfWgConf)'''