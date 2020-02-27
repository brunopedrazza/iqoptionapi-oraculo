from iqoptionapi.stable_api import IQ_Option
import time

EMAIL           = 'pedrazzabruno@gmail.com' #email de login
PASSWORD        = 'K5TmnxcAyRTh'            #senha da conta
ACCOUNT         = 'PRACTICE'                #PRACTICE/REAL

asset = 'EURUSD'

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
if all_assets['binary'][asset]['open']:
    amounts = []
    assets = []
    actions = []
    expiration_times = []
    digitals = []
    id_list = []
    amounts.append(50)
    assets.append(asset)
    actions.append('put')
    expiration_times.append(15)
    id_list=API.buy_multi(amounts,assets,actions,expiration_times)

    print("check win only one id (id_list[0])")
    print(API.check_win_v2(id_list[0]))
    
    