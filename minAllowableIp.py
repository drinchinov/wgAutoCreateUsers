import os, json, ipaddress

ip_range = "10.66.66.1/24"
listOfIpRange = list(ipaddress.ip_network(ip_range, False).hosts())
listOfFiles = os.listdir('./clients') 
listOfAllocatedIps = []

def getMinAllocatedIp():
    for el in listOfFiles:
        with open(f'./clients/{el}', 'r', encoding='utf-8') as f: #открыли файл с данными
            obj = json.load(f) #загнали все, что получилось в переменную
            interface = ''.join(obj['allocated_ips']).partition('/')[0]
            listOfAllocatedIps.append(ipaddress.ip_address(interface))

    listOfallowableIps = list(set(listOfIpRange) ^ set(listOfAllocatedIps))
    return min(listOfallowableIps)


print(getMinAllocatedIp())