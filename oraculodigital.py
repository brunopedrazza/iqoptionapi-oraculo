# -*- coding: utf-8 -*-
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
from decimal import Decimal
from multiprocessing import Process
import time
import sys

EMAIL = 'pedrazzabruno@gmail.com'  # email de login
PASSWORD = 'K5TmnxcAyRTh'  # senha da conta
CYCLE_DURATION = 15 # tempo de cada ciclo
EXPIRATION_TIME = 5  # tempo de expiração
ACTION = 'put'  # call/put
ACCOUNT = sys.argv[1].upper()  # PRACTICE/REAL/TOURNAMENT
AMOUNT = 200  # entrada em cada operação
MINIMUN_PAYOUT = 74  # payout mínimo pra fazer a entrada
GALES = 2  # quantidade de gales
OPERATIONS = {}  # lista de operações do dia
ALL_ASSETS = []  # lista com todos os ativos
INITIAL_BALANCE = 0 # banca inicial
STOP_WIN = 0.15 # stop-win

try:
    API = IQ_Option(EMAIL, PASSWORD)
    API.set_max_reconnect(5)
    API.change_balance(ACCOUNT)
except:
    print('Error defining API')
    
while True:
    if API.check_connect() == False:
        print('Not connected')
        API.connect()
    else:
        break
    time.sleep(1)
results_file = open('results/results_{}.txt'.format(sys.argv[2]),'a+')

class Operation:
  def __init__(self, asset, hour, minute):
    self.asset = asset
    self.hour = hour
    self.minute = minute
    self.profit = 0

def read_file():
    with open('files/{}.txt'.format(sys.argv[2])) as sinais_oraculo:
        lines = [line.split() for line in sinais_oraculo]
    for line in lines:
        asset = line[0]
        hour = line[1].split(':')[0]
        minute = line[1].split(':')[1]
        if minute not in OPERATIONS.keys():
            OPERATIONS[minute] = []
        OPERATIONS[minute].append(Operation(asset, hour, minute))
    last_operation = lines.pop()[1]
    return int(last_operation.split(':')[0]), int(last_operation.split(':')[1])

def single_operation(digital):
    while True:
        server_datetime = datetime.fromtimestamp(API.get_server_timestamp())
        if server_datetime.second == 58:
            id = API.buy_digital_spot(digital.asset, AMOUNT, ACTION, EXPIRATION_TIME)
            time.sleep((EXPIRATION_TIME - 1) * 60)
            break
        time.sleep(0.01)

    gales = 0
    while gales <= GALES:
        if id != 'error':
            line = '{} {}:{} '.format(digital.asset, digital.hour, digital.minute)
            while True:
                check, win = API.check_win_digital_v2(id)
                if check == True:
                    break
            if win < 0:
                if gales < GALES:
                    profit = digital.profit / 100
                    amount_gale = int((gales*(AMOUNT/profit) + (gales + 1) * AMOUNT + AMOUNT * profit) / profit)
                    id = API.buy_digital_spot(digital.asset, amount_gale, ACTION, EXPIRATION_TIME)
                    gales = gales + 1
                else:
                    line = line + 'LOSS'
                    print(line)
                    results_file.write(line + '\n')
                    break
            else:
                if gales == 0:
                    line = line + 'WIN'
                elif gales > 0:
                    line = line + 'GALE{}'.format(gales)
                print(line)
                results_file.write(line + '\n')
                break
    


def operate():
    ALL_ASSETS = API.get_all_open_time()
    
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

    digitals = []
    minute = ''

    if server_minute >= 0 and server_minute < 10:
        minute = '0' + str(server_minute)
    else:
        minute = str(server_minute)
    
    print('Operating {}:{}...'.format(str(server_hour), minute))

    for operation in OPERATIONS[minute]:
        if int(operation.hour) == server_hour and ALL_ASSETS['digital'][operation.asset]['open']:
            API.subscribe_strike_list(operation.asset,EXPIRATION_TIME)
            while True:
                profit_digital = API.get_digital_current_profit(operation.asset,EXPIRATION_TIME)
                if profit_digital > 0:
                    break
                time.sleep(1)
            API.unsubscribe_strike_list(operation.asset,EXPIRATION_TIME)
            operation.profit = profit_digital

            if operation.profit >= MINIMUN_PAYOUT:
                digitals.append(operation)
                print('Operation: {} {}:{} -> Option:Digital Payout:{} Amount:{}'.format(operation.asset, operation.hour, operation.minute, round(Decimal(operation.profit), 2), AMOUNT))

    if len(digitals) > 0:
        procs = []
        for digital in digitals:
            proc = Process(target=single_operation, args=(digital,))
            procs.append(proc)
            proc.start()
    else:
        print('No operations at this time')

if __name__ == "__main__":
    last_hour, last_minute = read_file()
    if len(OPERATIONS) > 0:
        INITIAL_BALANCE = API.get_balance()
        print('Initial {} balance: {}'.format(ACCOUNT, INITIAL_BALANCE))

        while True:
            now = datetime.now()
            if ((now.minute + 1) % CYCLE_DURATION) == 0 and now.second == 40:
                tic = time.perf_counter()
                operate()
                toc = time.perf_counter()
                time_to_sleep = CYCLE_DURATION * 60 - (toc - tic)
                time.sleep(time_to_sleep - 10)
                balance_now = API.get_balance()
                print(balance_now)
                # if balance_now >= INITIAL_BALANCE * (1 + STOP_WIN):
                #     print('Reached stop-win! Exiting program')
                #     results_file.close()
                #     sys.exit()
                now = datetime.now()
                if now.hour >= last_hour and now.minute > last_minute:
                    print('Last operation! Exiting program')
                    results_file.close()
                    sys.exit()
            time.sleep(1)

    else:
        print('Operations file is empty.')
