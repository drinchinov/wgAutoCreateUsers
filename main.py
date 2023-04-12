from transliterate import translit
import csv
import codecs
import json

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
for row in massOfVPNdicts:
    print(row)
    '''for key in row:
        if el == key:
            massOfWgConf.append(dict(zip(title_rows_listVPN, strVPN)))'''



