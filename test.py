from iqoptionapi.stable_api import IQ_Option
import time

EMAIL           = 'pedrazzabruno@gmail.com' #email de login
PASSWORD        = 'K5TmnxcAyRTh'            #senha da conta
ACCOUNT         = 'PRACTICE'                #PRACTICE/REAL

asset = 'NZDUSD'

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

all_assets = API.get_all_open_time()
profits = API.get_all_profit()

data = 'closed'
if all_assets['digital'][asset]['open']:
    API.subscribe_strike_list(asset,5)
    while True:
        data = API.get_digital_current_profit(asset,5)
        if data:
            break
        time.sleep(1)



print('{} -> Turbo = {}; Binary = {}; Digital = {}'.format(asset, all_assets['turbo'][asset]['open'], all_assets['binary'][asset]['open'], all_assets['digital'][asset]['open']))
print('{} -> Turbo = {}; Binary = {}; Digital = {}'.format(asset, profits[asset]['turbo'], profits[asset]['binary'], data))