'''
	BOT MHI v2
	- Analise em 1 minuto
	- Entradas para 1 minuto
	- Calcular as cores das velas de cada quadrado, ultimas 3 velas, minutos: 2, 3 e 4 / 7, 8 e 9
	- Entrar contra a maioria
  - Adicioando MHI2
  - Adicionado opção de binárias

	- Estrategia retirada do video https://www.youtube.com/watch?v=FePy1GY2wqQ
'''

from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
import time
import sys
import configparser
import pandas as pd


def remaining_seconds(minutes):
    return ((minutes * 60) - ((datetime.now().minute % minutes) * 60 + datetime.now().second)) - 30


def stop(lucro, gain, loss):
    if lucro <= float('-' + str(abs(loss))):
        print('Stop Loss batido!')
        sys.exit()

    if lucro >= float(abs(gain)):
        print('Stop Gain Batido!')
        sys.exit()


def entradas(par, entrada, direcao, operacao):
    status, id = API.buy_digital_spot(par, entrada, direcao, 1) if operacao == 1 else API.buy(
        entrada, par, direcao, 1)

    if status:
        while True:
            status, valor = API.check_win_digital_v2(id) if operacao == 1 else API.check_win_v3(id)
            if status:
                if valor > 0:
                    return status, round(valor, 2)
                else:
                    return status, round(valor, 2)
                break
    else:
        return False, 0


def payout(par):
    API.subscribe_strike_list(par, 1)
    while True:
        d = API.get_digital_current_profit(par, 1)
        if d != False:
            d = round(int(d) / 100, 2)
            break
        time.sleep(1)
    API.unsubscribe_strike_list(par, 1)

    return d


def get_payout(par):
    API.subscribe_strike_list(par, 1)
    while True:
        d = API.get_digital_current_profit(par, 1)
        if d:
            d = round(int(d) / 100, 2)
            break
        time.sleep(1)
    API.unsubscribe_strike_list(par, 1)

    return d


def get_balance():
    return API.get_balance()


def get_initial_amount(par, amount_by_payout):
    payout = get_payout(par)
    initial_percent = float(amount_by_payout[str(payout)]) / 100
    return round(initial_percent * capital_inicial, 2)


def configure():
    arquivo = configparser.RawConfigParser()
    arquivo.read('config.txt')

    return {'sorosgale': arquivo.get('GERAL', 'sorosgale'),
            'levels': arquivo.get('GERAL', 'levels'),
            'active': arquivo.get('GERAL', 'active'),
            'login': arquivo.get('GERAL', 'login'),
            'password': arquivo.get('GERAL', 'password')}


def get_candles_close(par):
    API.start_candles_stream(par, 60, 6)
    candles = API.get_realtime_candles(par, 60)

    df_time = pd.DataFrame([(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'), candles[ts]['close'],
                             candles[ts]['max'], candles[ts]['min']) for ts in
                            sorted(candles.keys(), reverse=True)],
                           columns=['from', 'close', 'max', 'min']).set_index('from')
    df_time = df_time.sort_index(ascending=False)
    df_time_close = df_time['close']
    return df_time_close


def ema(s, window):
    return pd.Series.ewm(s, span=window, min_periods=0, adjust=False, ignore_na=False).mean()[-1]


def mhi_strategy(par):
    velas = API.get_candles(par, 60, 6, time.time())

    velas[0] = 'g' if velas[0]['open'] < velas[0]['close'] else 'r' if velas[0]['open'] > velas[0]['close'] else 'd'
    velas[1] = 'g' if velas[1]['open'] < velas[1]['close'] else 'r' if velas[1]['open'] > velas[1]['close'] else 'd'
    velas[2] = 'g' if velas[2]['open'] < velas[2]['close'] else 'r' if velas[2]['open'] > velas[2]['close'] else 'd'
    velas[3] = 'g' if velas[3]['open'] < velas[3]['close'] else 'r' if velas[3]['open'] > velas[3]['close'] else 'd'
    velas[4] = 'g' if velas[4]['open'] < velas[4]['close'] else 'r' if velas[4]['open'] > velas[4]['close'] else 'd'
    velas[5] = 'g' if velas[5]['open'] < velas[5]['close'] else 'r' if velas[5]['open'] > velas[5]['close'] else 'd'

    cores = velas[0] + ' ' + velas[1] + ' ' + velas[2] + ' ' + velas[3] + ' ' + velas[4] + ' ' + velas[5]

    color_candles = 3
    green_count = cores.count('g')
    red_count = cores.count('r')
    if green_count < color_candles:
        return 'call'
    if red_count < color_candles:
        return 'put'
    else:
        return None


def verifica_direcao(par):
        df_time_close = get_candles_close(par)
        curr_ema = ema(df_time_close.iloc[0:100], ema_window)
        curr_price = df_time_close.iloc[0]
        mhi = mhi_strategy(par)
        result = 'call' if curr_price < curr_ema and mhi == 'call' else None
        result = 'put' if curr_price > curr_ema and mhi == 'put' else None
        return result

print('''
	     Simples MHI BOT
	  youtube.com/c/IQCoding
 ------------------------------------
''')

config = configure()

email = config['login']
pwd = config['password']

# REAL / PRACTICE
acc_type = 'PRACTICE'

API = IQ_Option(email, pwd)
API.connect()
API.change_balance('PRACTICE')  # PRACTICE / REAL

if API.check_connect():
    print(' Conectado com sucesso!')
else:
    print(' Erro ao conectar')
    # input('\n\n Aperte enter para sair')
    sys.exit()

operacao = int(1)  # int(input('\n Deseja operar na\n  1 - Digital\n  2 - Binaria\n  :: '))
tipo_mhi = int(1)  # int(input(' Deseja operar a favor da\n  1 - Minoria\n  2 - Maioria\n  :: '))

par = 'EURUSD'  # input(' Indique uma paridade para operar: ').upper()


capital_inicial = float(2000.0)

meta_diaria_ganho = float(100 / 100) * capital_inicial
meta_diaria_risco = float(100 / 100) * capital_inicial

stop_loss = meta_diaria_risco  # float(input(' Indique o valor de Stop Loss: '))
stop_gain = meta_diaria_ganho  # float(input(' Indique o valor de Stop Gain: '))

amount_by_payout = {'0.74': '0.99', '0.75': '0.97', '0.76': '0.96', '0.77': '0.94', '0.78': '0.93', '0.79': '0.91',
                    '0.80': '0.90', '0.81': '0.88', '0.82': '0.87', '0.83': '0.85', '0.84': '0.84', '0.85': '0.83',
                    '0.86': '0.82', '0.87': '0.80', '0.88': '0.79', '0.89': '0.78', '0.90': '0.77', '0.91': '0.76',
                    '0.92': '0.75', '0.93': '0.74', '0.94': '0.73', '0.95': '0.72', '0.96': '0.71', '0.97': '0.70',
                    '0.98': '0.69', '0.99': '0.68', '100': '0.67'}

valor_entrada = get_initial_amount(par, amount_by_payout)

valor_soros = 0
ema_window = 100
while True:
    minutos = 1
    entrar = remaining_seconds(minutos)

    if entrar < 15:
        print('\n\nIniciando operação!')
        print('Verificando cores..', end='')

        direcao = 'call'
        # if direcao:
        if direcao:
            print('Entrando com :', direcao)

            status, valor = entradas(par, valor_soros + valor_entrada, direcao, operacao)

            if valor < 0 and config['sorosgale'] == 'S':  # SorosGale

                lucro_total = 0
                lucro = 0
                perda = abs(valor)
                # Nivel
                for i in range(int(config['levels']) if int(config['levels']) > 0 else 1):
                    capital_inicial += lucro_total
                    # Mao
                    for i2 in range(2):

                        if lucro_total >= perda:
                            break

                        stop(lucro_total, stop_gain, stop_loss)

                        print('   SOROSGALE NIVEL ' + str(i + 1) + ' | MAO ' + str(i2 + 1) + ' | ', end='')

                        # Entrada
                        status, lucro = entradas(par, perda / 2 + lucro, direcao, minutos)

                        print(status, '/', lucro, '\n')

                        if lucro > 0:
                            lucro_total += lucro
                        elif lucro < 0:
                            lucro_total = 0
                            perda += perda / 2
                            break
            elif valor > 0:
                capital_inicial += valor

            time.sleep(minutos * 60)
