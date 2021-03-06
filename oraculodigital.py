# -*- coding: utf-8 -*-
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
from decimal import Decimal
from multiprocessing import Process
import time
import sys
from credentials import Credentials

ACCOUNT = sys.argv[1].upper()  # PRACTICE/REAL/TOURNAMENT
FILE_NAME = sys.argv[2] # nome do arquivo
AMOUNT = int(sys.argv[3])  # entrada em cada operação
GALES = int(sys.argv[4])  # quantidade de gales
STOP_WIN = int(sys.argv[5])  # stop-win

EMAIL = Credentials().email  # email de login
PASSWORD = Credentials().password  # senha da conta
CYCLE_DURATION = 15  # tempo de cada ciclo
EXPIRATION_TIME = 5  # tempo de expiração
ACTION = 'put'  # call/put
MINIMUN_PAYOUT = 74  # payout mínimo pra fazer a entrada
OPERATIONS = {}  # lista de operações do dia
ALL_ASSETS = []  # lista com todos os ativos
INITIAL_BALANCE = 0  # banca inicial

while True:
    try:
        print('Trying to connect...')
        API = IQ_Option(EMAIL, PASSWORD)
        API.set_max_reconnect(5)
        API.change_balance(ACCOUNT)
    except:
        print('Error defining API, trying again')
        continue
    break

while True:
    if API.check_connect() == False:
        print('Not connected')
        API.connect()
    else:
        print('Connected')
        break
    time.sleep(1)
results_file = open('results/results_{}.txt'.format(FILE_NAME), 'a+')


class Operation:
    def __init__(self, asset, hour, minute):
        self.asset = asset
        self.hour = hour
        self.minute = minute
        self.profit = 0


def read_file():
    with open('files/{}.txt'.format(FILE_NAME)) as sinais_oraculo:
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
                if check:
                    break
            if win < 0:
                if gales < GALES:
                    amount_gale = (-1 * win) * 2.1
                    # profit = digital.profit / 100
                    # amount_gale = int((gales*(AMOUNT/profit) + (gales + 1) * AMOUNT + AMOUNT * profit) / profit)
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
    while True:
        try:
            ALL_ASSETS = API.get_all_open_time()
        except:
            print('Error defining getting ALL OPEN TIME, trying again...')
            continue
        break

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

    if 0 <= server_minute < 10:
        minute = '0' + str(server_minute)
    else:
        minute = str(server_minute)

    print('Operating {}:{}'.format(str(server_hour), minute))

    for operation in OPERATIONS[minute]:
        if int(operation.hour) == server_hour and ALL_ASSETS['digital'][operation.asset]['open']:
            API.subscribe_strike_list(operation.asset, EXPIRATION_TIME)
            while True:
                profit_digital = API.get_digital_current_profit(operation.asset, EXPIRATION_TIME)
                if profit_digital > 0:
                    break
                time.sleep(1)
            API.unsubscribe_strike_list(operation.asset, EXPIRATION_TIME)
            operation.profit = profit_digital

            if operation.profit >= MINIMUN_PAYOUT:
                digitals.append(operation)
                print(
                    'Operation: {} {}:{} -> Option:Digital Payout:{} Amount:{}'.format(operation.asset, operation.hour,
                                                                                       operation.minute,
                                                                                       round(Decimal(operation.profit),
                                                                                             2), AMOUNT))

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
        print('Stop win: {}'.format(STOP_WIN))
        print('Initial {} balance: {}'.format(ACCOUNT, INITIAL_BALANCE))
        while True:
            now = datetime.now()
            if ((now.minute + 1) % CYCLE_DURATION) == 0 and (now.second == 39 or now.second == 40):
                tic = time.perf_counter()
                operate()
                toc = time.perf_counter()
                time_to_sleep = CYCLE_DURATION * 60 - (toc - tic)
                time.sleep(time_to_sleep - 10)
                balance_now = API.get_balance()
                print(balance_now)
                now = datetime.now()
                if balance_now >= STOP_WIN:
                    print('STOP WIN')
                    results_file.close()
                    sys.exit()
                if now.hour == 17:
                    print('Last operation! Exiting program')
                    results_file.close()
                    sys.exit()
            time.sleep(1)

    else:
        print('Operations file is empty.')
