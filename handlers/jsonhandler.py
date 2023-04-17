import codecs, os, ipaddress, getters
from transliterate import translit
from datetime import datetime

class CsvConverter:
    def __init__(self, file_vpn_users_attributes, path_to_file_vpn_users):
        self.file_vpn_users_attributes = file_vpn_users_attributes
        self.path_to_file_vpn_users = path_to_file_vpn_users

    def convert_file_to_list_of_json(self):
        list_of_json = []

        with codecs.open(self.path_to_file_vpn_users, "r", "utf_8_sig" ) as vpn_users_from_file:

            list_vpn_users = vpn_users_from_file.read().split('\n')
            vpn_users_from_file.close()

        for row in list_vpn_users:
            str_of_list_vpn_users = row.split(',')
            if len(str_of_list_vpn_users) == 5:
                list_of_json.append(dict(zip(self.file_vpn_users_attributes, str_of_list_vpn_users)))

        return list_of_json
    
def get_newJSONconf(massOfVPNdicts, title_rows_dbClients, nowParse, listAllocatedIp, allowedIp, prefixOfAllowedIp)
    
class JsonHandler:
    def __init__(self, list_of_json, client_attributes, formatted_datetime_now, list_of_allocated_ips, allowed_ips, prefix_of_allowed_ip):
        self.list_of_json = list_of_json
        self.client_attributes = client_attributes
    
    def get_new_clients_json(self, formatted_datetime_now, list_of_allocated_ips, allowed_ips, prefix_of_allowed_ip):

        list_of_wgconf = []

        for row in self.list_of_json: 
            element_of_wgconf = {}
            privateKey, public_key, preshared_key = generate_keys()
            for el in self.client_attributes:
                try:
                    element_of_wgconf[el] = get_translit_string(row[el])
                except:

                    if el == 'id':
                        idOfRow = get_translit_string(row['name']) + '_' + get_translit_string(row['email'])
                        element_of_wgconf[el] = idOfRow

                    elif el == 'private_key':
                        element_of_wgconf[el] = privateKey

                    elif el == 'public_key':
                        element_of_wgconf[el] = public_key

                    elif el == 'preshared_key':
                        element_of_wgconf[el] = preshared_key

                    elif el == 'allocated_ips':
                        minAllocatedIp = min(list_of_allocated_ips)
                        element_of_wgconf[el] = [format(ipaddress.IPv4Address(minAllocatedIp)) + '/' + prefix_of_allowed_ip]
                        list_of_allocated_ips.remove(minAllocatedIp)

                    elif el == 'allowed_ips':
                        element_of_wgconf[el] = [allowed_ips]

                    elif el == 'extra_allowed_ips':
                        element_of_wgconf[el] = []

                    elif el == 'use_server_dns':
                        element_of_wgconf[el] = True

                    elif el == 'enabled':
                        element_of_wgconf[el] = True

                    elif el == 'created_at' or el == 'updated_at':
                        element_of_wgconf[el] =  nowParse

                    else:
                        element_of_wgconf[el] = None

            list_of_wgconf.append(element_of_wgconf)

        return list_of_wgconf
        


