from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
import time

email           = 'pedrazzabruno@gmail.com' #email de login
password        = 'K5TmnxcAyRTh'            #senha da conta
expiration_time = 5                         #tempo de expiração
action          = 'put'                     #call/put
account         = 'PRACTICE'                #PRACTICE/REAL
ammount         = 100                       #entrada em cada operação
minimum_payout  = 0.5                       #payout mínimo pra fazer a entrada

API = IQ_Option(email, password)
API.set_max_reconnect(5)
API.change_balance(account)

while True:
    if API.check_connect() == False:
        print('Not connected.')
        API.connect()
    else:
        print('Connected.')
        break

    time.sleep(1)

Money=[]
ACTIVES=[]
ACTION=[]
expirations_mode=[]
mult = 1

ALL_Asset = API.get_all_open_time()
profits = API.get_all_profit()

for type_name, data in ALL_Asset.items():
    for Asset,value in data.items():
        if (type_name == 'turbo' and value['open'] == True):
            print(type_name,Asset,value["open"],profits[Asset][type_name])
            if (profits[Asset][type_name] >= minimum_payout):
                Money.append(mult * ammount)
                mult = mult + 1
                ACTION.append("call")
                expirations_mode.append(expiration_time)
                ACTIVES.append(Asset)
                # buy = API.buy(200,Asset,action,expiration_time)
                # success = buy[0]
                # id = buy[1]
                # print(success, id)

print(API.get_balance())
if (len(ACTIVES) > 0):
    while True:
        server_datetime = datetime.fromtimestamp(API.get_server_timestamp())
        hour, minute, second = server_datetime.hour, server_datetime.minute, server_datetime.second
        if (hour == 1 and minute == 12 and second == 59):
            break
        time.sleep(0.01)
id_list = API.buy_multi(Money,ACTIVES,ACTION,expirations_mode)
print(id_list)
print(API.get_balance())
