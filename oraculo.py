# -*- coding: utf-8 -*-
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
import time
import sys
import schedule

EMAIL           = 'pedrazzabruno@gmail.com' #email de login
PASSWORD        = 'K5TmnxcAyRTh'            #senha da conta
EXPIRATION_TIME = 5                         #tempo de expiração
ACTION          = 'put'                     #call/put
ACCOUNT         = 'PRACTICE'                #PRACTICE/REAL
AMMOUNT         = 100                        #entrada em cada operação
MINIMUN_PAYOUT  = 0.5                      #payout mínimo pra fazer a entrada
operations      = []                        #lista de operações do dia
class Operation:
  def __init__(self, asset, hour, minute):
    self.asset = asset
    self.hour = hour
    self.minute = minute

def read_file():
    with open('files/{}.txt'.format(sys.argv[1])) as sinais_oraculo:
        lines = [line.split() for line in sinais_oraculo]
    for line in lines:
        asset = line[0]
        hour = line[1].split(':')[0]
        minute= line[1].split(':')[1]
        operations.append(Operation(asset, hour, minute))

def operate():
    all_assets = API.get_all_open_time()
    profits = API.get_all_profit()
    ammounts = []
    assets = []
    actions = []
    expiration_times = []

    for operation in operations:
        server_datetime = datetime.fromtimestamp(API.get_server_timestamp())
        server_hour = server_datetime.hour
        server_minute = server_datetime.minute
        if server_minute == 59:
            server_minute = 0
            server_hour = server_hour + 1
        else:
            server_minute = server_minute + 1 
        if operation.hour == server_hour and operation.minute == server_minute and all_assets['turbo'][operation.asset]['open'] and profits[operation.asset]['turbo'] >= MINIMUN_PAYOUT:
            assets.append(operation.asset)
            actions.append(ACTION)
            ammounts.append(AMMOUNT)
            expiration_times.append(EXPIRATION_TIME)
            operations.remove(operation)
    
    if len(assets) > 0:
        while True:
            server_datetime = datetime.fromtimestamp(API.get_server_timestamp())
            if (server_datetime.second == 59):
                id_list = API.buy_multi(ammounts,assets,actions,expiration_times)
                break
            time.sleep(0.01)
        print(id_list)
        print('Operated')
    
    else:
        print('No operations at this time')

    print(API.get_balance())

read_file()

API = IQ_Option(EMAIL, PASSWORD)
API.set_max_reconnect(5)
API.change_balance(ACCOUNT)

while True:
    if API.check_connect() == False:
        print('Not connected.')
        API.connect()
    else:
        print('Connected.')
        break

    time.sleep(1)

print(API.get_balance())

while True:
    if ((datetime.now().minute + 1) % 15) == 0 and datetime.now().second == 40:
        print('Started')
        operate()
        schedule.every(15).minutes.do(operate)
        break
    time.sleep(1)

while True:
    schedule.run_pending()
    time.sleep(1)


# for type_name, data in ALL_Asset.items():
#     for Asset,value in data.items():
#         if (type_name == 'turbo' and value['open'] == True):
#             print(type_name,Asset,value["open"],profits[Asset][type_name])
#             if (profits[Asset][type_name] >= minimum_payout):
#                 Money.append(mult * ammount)
#                 mult = mult + 1
#                 ACTION.append("call")
#                 expirations_mode.append(expiration_time)
#                 ACTIVES.append(Asset)
#                 # buy = API.buy(200,Asset,action,expiration_time)
#                 # success = buy[0]
#                 # id = buy[1]
#                 # print(success, id)

# if (len(ACTIVES) > 0):
#     while True:
#         server_datetime = datetime.fromtimestamp(API.get_server_timestamp())
#         hour, minute, second = server_datetime.hour, server_datetime.minute, server_datetime.second
#         print(hour, minute, second)
#         if (hour == 12 and minute == 10 and second == 59):
#             break
#         time.sleep(0.01)
# id_list = API.buy_multi(Money,ACTIVES,ACTION,expirations_mode)
# print(id_list)
