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
ACCOUNT         = 'TOURNAMENT'              #PRACTICE/REAL
AMOUNT          = 35                        #entrada em cada operação
MINIMUN_PAYOUT  = 65                        #payout mínimo pra fazer a entrada
GALES           = 1                         #quantidade de gales
OPERATIONS      = []                        #lista de operações do dia
ALL_ASSETS      = []                        #lista com todos os ativos
PROFITS         = []                        #payouts dos ativos
class Operation:
  def __init__(self, asset, hour, minute):
    self.asset = asset
    self.hour = hour
    self.minute = minute
    self.option = ''
    self.profit = 0

def read_file():
    with open('files/{}.txt'.format(sys.argv[1])) as sinais_oraculo:
        lines = [line.split() for line in sinais_oraculo]
    for line in lines:
        asset = line[0]
        hour = int(line[1].split(':')[0])
        minute = int(line[1].split(':')[1])
        OPERATIONS.append(Operation(asset, hour, minute))

def operate():
    amounts = []
    assets = []
    actions = []
    expiration_times = []
    digitals = []

    for operation in OPERATIONS:
        server_datetime = datetime.fromtimestamp(API.get_server_timestamp())
        server_hour = int(server_datetime.hour)
        server_minute = int(server_datetime.minute)
        if server_minute == 59:
            server_minute = 0
            server_hour = server_hour + 1
        else:
            server_minute = server_minute + 1

        if operation.hour == server_hour and operation.minute == server_minute and (ALL_ASSETS['digital'][operation.asset]['open'] or ALL_ASSETS['turbo'][operation.asset]['open']):
            if ALL_ASSETS['turbo'][operation.asset]['open']:
                operation.option = 'turbo'
                operation.profit = PROFITS[operation.asset]['turbo'] * 100

            if ALL_ASSETS['digital'][operation.asset]['open']:
                API.subscribe_strike_list(operation.asset,5)
                while True:
                    profit_digital = API.get_digital_current_profit(operation.asset,5)
                    if profit_digital:
                        break
                    time.sleep(0.5)
                if (profit_digital > operation.profit):
                    operation.option = 'digital'
                    operation.profit = profit_digital
            
            if ACCOUNT == 'TOURNAMENT':
                if ALL_ASSETS['turbo'][operation.asset]['open']:
                    operation.option = 'turbo'
                    operation.profit = PROFITS[operation.asset]['turbo'] * 100
                else:
                    continue

            if operation.profit >= MINIMUN_PAYOUT:
                if operation.option == 'turbo':
                    assets.append(operation.asset)
                    actions.append(ACTION)
                    amounts.append(AMOUNT)
                    expiration_times.append(EXPIRATION_TIME)
                else:
                    digitals.append(operation)
                print('Operation: {} -> {}:{}, Option: {}, Profit: {}'.format(operation.asset, operation.hour, operation.minute, operation.option, operation.profit))
    
    id_list = []

    if len(digitals) > 0 or len(assets) > 0:
        while True:
            server_datetime = datetime.fromtimestamp(API.get_server_timestamp())
            if (server_datetime.second == 59):
                if len(assets) > 0:
                    id_list = API.buy_multi(amounts,assets,actions,expiration_times)
                if len(digitals) > 0:
                    for digital in digitals:
                        id = API.buy_digital_spot(digital.asset,AMOUNT,ACTION,EXPIRATION_TIME)
                        id_list.append(id)
                break
            time.sleep(0.01)

    if len(id_list) > 0:
        print(id_list)
        print('Operated {} times'.format(len(id_list)))
    else:
        print('No operations at this time')

    time.sleep(5)
    balance_before = API.get_balance()
    print('Balance before: {}'.format(balance_before))


read_file()

if len(OPERATIONS) > 0:
    API = IQ_Option(EMAIL, PASSWORD)
    API.set_max_reconnect(5)
    API.change_balance(ACCOUNT)

    while True:
        if API.check_connect() == False:
            print('Not connected')
            API.connect()
        else:
            print('{} account connected'.format(ACCOUNT))
            break

        time.sleep(1)

    print('{} balance: {}'.format(ACCOUNT, API.get_balance()))

    while True:
        if ((datetime.now().minute + 1) % 15) == 0 and datetime.now().second == 20:
        #if (datetime.now().minute + 1) == 55 and datetime.now().second == 20:
            while True:
                try:
                    ALL_ASSETS = API.get_all_open_time()
                    PROFITS = API.get_all_profit()
                    break
                except:
                    print('Trying to get all assets and profits again...')
                    pass
            print('All assets and profits have been picked')
        if ((datetime.now().minute + 1) % 15) == 0 and datetime.now().second == 40:
        #if (datetime.now().minute + 1) == 55 and datetime.now().second == 40:
            print('Cycle started')
            operate()
            schedule.every(15).minutes.do(operate)
            break
        time.sleep(1)

    while True:
        schedule.run_pending()
        time.sleep(1)

else:
    print('Operations file is empty.')
