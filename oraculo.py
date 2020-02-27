# -*- coding: utf-8 -*-
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
import time
import sys
import schedule

EMAIL = 'pedrazzabruno@gmail.com'  # email de login
PASSWORD = 'K5TmnxcAyRTh'  # senha da conta
CYCLE_DURATION = 15 # tempo de cada ciclo
EXPIRATION_TIME = 5  # tempo de expiração
ACTION = 'put'  # call/put
ACCOUNT = sys.argv[1].upper()  # PRACTICE/REAL/TOURNAMENT
AMOUNT = 40  # entrada em cada operação
MINIMUN_PAYOUT = 74  # payout mínimo pra fazer a entrada
GALES = 1  # quantidade de gales
OPERATIONS = {
    '00': [],
    '15': [],
    '30': [],
    '45': []
}  # lista de operações do dia
ALL_ASSETS = []  # lista com todos os ativos
PROFITS = []  # payouts dos ativos
INITIAL_BALANCE = 0
LAST_OPERATION_HOUR = ''

class Operation:
  def __init__(self, asset, hour, minute):
    self.asset = asset
    self.hour = hour
    self.minute = minute
    self.option = ''
    self.profit = 0

def organize_operations(operation):
    OPERATIONS[operation.minute].append(operation)

def read_file():
    with open('files/{}.txt'.format(sys.argv[2])) as sinais_oraculo:
        lines = [line.split() for line in sinais_oraculo]
    for line in lines:
        asset = line[0]
        hour = line[1].split(':')[0]
        minute = line[1].split(':')[1]
        organize_operations(Operation(asset, hour, minute))
    LAST_OPERATION_HOUR = lines.pop()[1]
    print(LAST_OPERATION_HOUR)


def operate():
    print(datetime.fromtimestamp(API.get_server_timestamp()))
    ALL_ASSETS = API.get_all_open_time()
    PROFITS = API.get_all_profit()

    print('All assets and profits have been picked')
    print('Operating...')

    server_datetime = datetime.fromtimestamp(API.get_server_timestamp())
    server_hour = server_datetime.hour
    server_minute = server_datetime.minute
    if server_minute == 59:
        server_minute = 0
        if server_hour == 23:
            server_hour = 0
        else:
            server_hour = server_hour + 1
    else:
        server_minute = server_minute + 1

    amounts = []
    assets = []
    actions = []
    expiration_times = []
    digitals = []
    minute = ''

    if server_minute >= 0 and server_minute < 10:
        minute = '0' + str(server_minute)
    else:
        minute = str(server_minute)

    for operation in OPERATIONS[minute]:
        if int(operation.hour) == server_hour and (ALL_ASSETS['digital'][operation.asset]['open'] or ALL_ASSETS['turbo'][operation.asset]['open']):
            if ALL_ASSETS['turbo'][operation.asset]['open']:
                operation.option = 'turbo'
                operation.profit = PROFITS[operation.asset]['turbo'] * 100

            if ALL_ASSETS['digital'][operation.asset]['open']:
                API.subscribe_strike_list(operation.asset,EXPIRATION_TIME)
                while True:
                    profit_digital = API.get_digital_current_profit(operation.asset,EXPIRATION_TIME)
                    if profit_digital > 0:
                        break
                    time.sleep(1)
                API.unsubscribe_strike_list(operation.asset,EXPIRATION_TIME)
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
                print('Operation: {} {}:{} -> Option:{} Payout:{} Amount:{}'.format(operation.asset,
                                                                                    operation.hour, operation.minute, operation.option, operation.profit, AMOUNT))

    id_list_digital = []
    id_list_turbo = []
    operations = len(digitals) + len(assets)
    #id_gale1_list_turbo = []
    if operations > 0:
        second = 59
        if len(digitals) == 1:
            second = 58
        elif len(digitals) > 1:
            second = 57
        while True:
            server_datetime = datetime.fromtimestamp(
                API.get_server_timestamp())
            if server_datetime.second == second:
                if len(digitals) > 0:
                    for digital in digitals:
                        id = API.buy_digital_spot(
                            digital.asset, AMOUNT, ACTION, EXPIRATION_TIME)
                        id_list_digital.append([id, digital, GALES])
                if len(assets) > 0:
                    id_list_turbo = API.buy_multi(
                        amounts, assets, actions, expiration_times)
                print('Waiting for win or loss...')
                time.sleep((EXPIRATION_TIME - 1) * 60)
                while len(id_list_digital) > 0:
                    id_digital = id_list_digital.pop(0)
                    id = id_digital[0]
                    digital = id_digital[1]
                    gales = id_digital[2]
                    if id != 'error' and gales > 0:
                        while True:
                            check, win = API.check_win_digital_v2(id)
                            if check == True:
                                break
                        if win < 0:
                            id = API.buy_digital_spot(digital.asset, int(AMOUNT * (GALES - gales + 1) * 2), ACTION, EXPIRATION_TIME)
                            operations = operations + 1
                            id_list_digital.append([id, digital, gales - 1])
                        else:
                            print('{} -> WIN'.format(digital.asset))
                break
            time.sleep(0.01)

    if operations > 0:
        print('Operated {} times'.format(operations))
    else:
        print('No operations at this time')

    time.sleep(10)
    balance_before = API.get_balance()
    print('Balance before: {}'.format(balance_before))


if __name__ == "__main__":
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

        INITIAL_BALANCE = API.get_balance()
        print('{} balance: {}'.format(ACCOUNT, INITIAL_BALANCE))

        while True:
            now = datetime.now()
            print(now)
            if ((now.minute + 1) % CYCLE_DURATION) == 0 and now.second == 40:
                print('Entrou')
                tic = time.perf_counter()
                operate()
                toc = time.perf_counter()
                time_to_sleep = CYCLE_DURATION * 60 - (toc - tic)
                print('Sleeping for {} minutes'.format(time_to_sleep/60))
                time.sleep(time_to_sleep - 15)
                balance_before = 
            time.sleep(1)

    else:
        print('Operations file is empty.')
