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
import pickle


def is_asset_open(asset, all_opened_assets, mode):
    return all_opened_assets[mode][asset]['open']


def get_all_opened_assets():
    return API.get_all_open_time()


def remaining_seconds(minutes):
    return ((minutes * 60) - ((datetime.now().minute % minutes) * 60 + datetime.now().second)) - 30


def stop(lucro, gain, loss):
    if lucro <= float('-' + str(abs(loss))):
        print('Stop Loss batido!')
        sys.exit()

    if lucro >= float(abs(gain)):
        print('Stop Gain Batido!')
        sys.exit()


def entradas(par, entrada, direcao, minutos):
    status, id = API.buy_digital_spot(par, entrada, direcao, minutos) if operacao == 0 else API.buy(entrada, par,
                                                                                                    direcao, minutos)

    if status:
        while True:
            resultado, valor = API.check_win_digital_v2(id) if operacao == 0 else API.check_win_v3(id)

            if resultado and valor:
                if valor > 0:
                    return 'win', valor
                elif valor < 0:
                    return 'loss', 0
    else:
        return 'error', 0


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


def capital_por_ativo(num_ativos, alavancagem):
    capital = get_balance()
    capital_ativo = capital / num_ativos
    return round(capital_ativo * alavancagem, 2)


def get_initial_amount(ativo, valor_por_payout, capital):
    payout = get_payout(ativo)
    initial_percent = round(float(valor_por_payout[str(payout)]) / 100, 2)
    capital = round(capital, 2)
    entrada = round(initial_percent * capital, 2)
    return entrada


def configure():
    arquivo = configparser.RawConfigParser()
    arquivo.read('config.txt')

    return {'sorosgale': arquivo.get('GERAL', 'sorosgale'),
            'levels': arquivo.get('GERAL', 'levels'),
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


def get_opened_actives_list(actives):
    opened_assets = get_all_opened_assets()
    opened = dict()
    for mode in ['turbo', 'digital', 'binary']:
        for active in actives:
            if is_asset_open(active, opened_assets, mode):
                opened[mode] = active

    return opened


def vc_strategy(df, window, min_periods, multiplier, nivel_1, nivel_2, touch_type):
    df['aux_median'] = (df['max'] + df['min']) / 2
    df['Floating Axis'] = df['aux_median'].rolling(window=window, min_periods=min_periods, closed='right').mean()
    df['Relative Open'] = df['open'] - df['Floating Axis']
    df['Relative Close'] = df['close'] - df['Floating Axis']
    df['Relative High'] = df['max'] - df['Floating Axis']
    df['Relative Low'] = df['min'] - df['Floating Axis']

    df['aux_diff'] = (df['max'] - df['min']) * multiplier
    df['Floating Axis'] = df['aux_median'].rolling(window=window, min_periods=min_periods, closed='right').mean()
    df['Volatility Unit'] = df['aux_diff'].rolling(window=window, min_periods=min_periods, closed='right').mean()

    df['V Chart Open'] = (df['open'] - df['Floating Axis']) / df['Volatility Unit']
    df['V Chart Close'] = (df['close'] - df['Floating Axis']) / df['Volatility Unit']
    df['V Chart High'] = (df['max'] - df['Floating Axis']) / df['Volatility Unit']
    df['V Chart Low'] = (df['min'] - df['Floating Axis']) / df['Volatility Unit']

    if touch_type == 'close':
        df['signal'] = df.apply(lambda x: 'buy' if x['V Chart Close'] <= -nivel_1 else 'sell' if x[
                                                                                                     'V Chart Close'] >= nivel_2 else 'nothing',
                                axis=1)
    elif touch_type == 'pavio':
        df['signal'] = df.apply(
            lambda x: 'buy' if x['V Chart Low'] <= -nivel_1 else 'sell' if x['V Chart High'] >= nivel_2 else 'nothing',
            axis=1)

    return df.iloc[-1]['signal']


def donchian_fractal(par, timeframe):
    velas = API.get_candles(par, timeframe, 21, time.time())
    taxas_min = []
    taxas_max = []

    for candles in velas:
        taxas_min.append(round(candles['min'], 6))
        taxas_max.append(round(candles['max'], 6))

    # Donchian
    maior = sorted(taxas_max, reverse=True)[0]
    menor = sorted(taxas_min)[0]

    # Fractal
    fractal = None
    if velas[-2]['max'] > velas[-3]['max'] and velas[-2]['max'] > velas[-1]['max']:
        fractal = 'acima'
    elif velas[-2]['min'] < velas[-3]['min'] and velas[-2]['min'] < velas[-1]['min']:
        fractal = 'abaixo'

    # Ultimas 3 velas respeitam os limites do Donchian
    limite_acima = False if velas[-1]['max'] > maior or velas[-2]['max'] > maior or velas[-3]['max'] > maior else True
    limite_abaixo = False if velas[-1]['min'] < menor or velas[-2]['min'] < menor or velas[-3]['min'] < menor else True

    if fractal is not None:

        if fractal == 'acima' and round(velas[-2]['max'], 6) >= maior and limite_acima:
            return 'put'

        elif fractal == 'abaixo' and round(velas[-2]['min'], 6) <= menor and limite_abaixo:
            return 'call'


def verifica_direcao(par):
    df_time_close = get_candles_close(par)
    curr_price = df_time_close.iloc[0]
    min_periods = 5  # int(st.iloc[0]['min_periods'])
    multiplier = 0.2  # float(st.iloc[0]['multiplier'])
    nivel_1 = 7  # int(st.iloc[0]['nivel_1'])
    nivel_2 = 7  # int(st.iloc[0]['nivel_2'])
    touch_type = 'pavio'  # st.iloc[0]['touch_type']
    window = 5  # int(st.iloc[0]['window'])

    API.start_candles_stream('EURUSD', 60, 51)
    candles = API.get_realtime_candles('EURUSD', 60)

    df_time = pd.DataFrame(
        [(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'), candles[ts]["open"], candles[ts]["close"],
          candles[ts]["max"], candles[ts]["min"]) for ts in
         sorted(candles.keys(), reverse=True)],
        columns=['from', 'open', 'close', 'max', 'min']).set_index('from')
    df_time = df_time.sort_index(ascending=True)

    direcao = vc_strategy(df_time, window, min_periods, multiplier, nivel_1, nivel_2, touch_type)

    return direcao


def get_active(actives, operacao):
    open_actives = get_opened_actives_list(actives)
    modes = ['digital', 'binary']
    return open_actives.get(modes[operacao])


def save_gale(gale_level_0, gale_level_1, amount, result):
    file = open("gales_data.pickle", "wb")

    my_dict = {"gale_level_0": gale_level_0,
               "gale_level_1": gale_level_1,
               "result": result,
               "amount": amount}

    # serializing dictionary
    pickle.dump(my_dict, file)

    # closing the file
    file.close()


def get_gale():
    # reading the data from the file
    with open('gales_data.pickle', 'rb') as handle:
        data = handle.read()

    print("Data type before reconstruction : ", type(data))

    return pickle.loads(data)


def reset_gale():
    file = open("gales_data.pickle", "wb")
    my_dict = {"gale_level_0": 0,
               "gale_level_1": 0,
               "result": 'win',
               "amount": 4.00}

    # serializing dictionary
    pickle.dump(my_dict, file)

    # closing the file
    file.close()


print('''
	     Simples MHI BOT
	  youtube.com/c/IQCoding
 ------------------------------------
''')

config = configure()

email = config['login']
pwd = config['password']

# REAL / PRACTICE
API = IQ_Option(email, pwd)
API.connect()
API.change_balance('PRACTICE')  # PRACTICE / REAL

if API.check_connect():
    print(' Conectado com sucesso!')
else:
    print(' Erro ao conectar')
    # input('\n\n Aperte enter para sair')
    sys.exit()

tipo_mhi = int(1)  # int(input(' Deseja operar a favor da\n  1 - Minoria\n  2 - Maioria\n  :: '))

actives = ['EURUSD', 'EURUSD-OTC']
mode = ['digital', 'binary']
operacao = 0  # int('\n Deseja operar na\n  0 - Digital\n  1 - Binaria\n  :: '))

n_ativos = 5
alavancagem = 3

capital_inicial = capital_por_ativo(n_ativos, alavancagem)
meta_diaria_ganho = round(float(3.5 / 100) * capital_inicial, 2)
meta_diaria_risco = round(float(3.0 / 100) * capital_inicial, 2)

stop_loss = meta_diaria_risco  # float(input(' Indique o valor de Stop Loss: '))
stop_gain = meta_diaria_ganho  # float(input(' Indique o valor de Stop Gain: '))

expiration = 1

amount_by_payout = {'0.74': '0.99', '0.75': '0.97', '0.76': '0.96', '0.77': '0.94', '0.78': '0.93', '0.79': '0.91',
                    '0.80': '0.90', '0.81': '0.88', '0.82': '0.87', '0.83': '0.85', '0.84': '0.84', '0.85': '0.83',
                    '0.86': '0.82', '0.87': '0.80', '0.88': '0.79', '0.89': '0.78', '0.90': '0.77', '0.91': '0.76',
                    '0.92': '0.75', '0.93': '0.74', '0.94': '0.73', '0.95': '0.72', '0.96': '0.71', '0.97': '0.70',
                    '0.98': '0.69', '0.99': '0.68', '100': '0.67'}

ema_window = 100

while True:

    capital_atual = capital_por_ativo(n_ativos, alavancagem)
    par = get_active(actives, operacao)
    data_gale = get_gale()
    loop_level_0 = int(config['levels']) - int(data_gale["gale_level_0"])
    in_loop = 0 < int(data_gale["gale_level_0"]) < int(config['levels'])
    if loop_level_0 == 0:
        reset_gale()

    data_gale = get_gale()

    if par:
        valor_entrada = 4.0  # get_initial_amount(par, amount_by_payout, capital_atual)

    entrar = API.get_remaning(expiration)
    direcao = donchian_fractal(par, 60)

    if datetime.now().minute == 15:
        print('    Operando com par ', par, ' direcao ', direcao, ' valor ', valor_entrada, 'tempo restante ', entrar,
              '\n')

    direcao = 'call'
    if direcao:
        # if 30 < entrar < 60 and direcao:

        print('    Entrando com :', direcao, ' ativo ', par, ' valor ', valor_entrada)

        if data_gale["gale_level_0"] == 0:
            resultado, valor = entradas(par, valor_entrada, direcao, expiration)
            data_gale["result"] = resultado

        if in_loop or (resultado == 'loss' and config['sorosgale'] == 'S'):  # SorosGale

            lucro_total = 0
            lucro = 0
            perda = valor_entrada

            data_gale["amount"] = perda / 2 + lucro

            # Nivel
            for i in range(int(config['levels']) - int(data_gale["gale_level_0"])):

                # Mao
                for i2 in range(2 - int(data_gale["gale_level_1"])):

                    # Entrada
                    while True:
                        if lucro_total >= perda:
                            reset_gale()
                            break

                        # capital_inicial += round(lucro_total - perda, 2)

                        stop(round(lucro_total - perda, 2), meta_diaria_ganho, meta_diaria_risco)

                        entrar = API.get_remaning(expiration)
                        direcao = donchian_fractal(par, 60)

                        direcao = 'call'
                        if direcao:
                            # if 30 < entrar < 60 and direcao:

                            print('    SOROSGALE NIVEL ' + str(i + 1) + ' | MAO ' + str(i2 + 1) + ' | \n', end=' ')

                            resultado, lucro = entradas(par, data_gale["amount"], direcao, expiration)

                            if resultado:
                                print(resultado, '/', lucro, ' ', perda, '\n')
                                if resultado == 'win':
                                    lucro_total += round(lucro, 2)
                                    save_gale((i + 1), (i2 + 1), (perda / 2 + lucro), resultado)
                                    data_gale = get_gale()
                                elif resultado == 'loss':
                                    lucro_total = 0
                                    perda += round(perda / 2, 2)
                                    save_gale((i + 1), (i2 + 1), (perda / 2 + lucro), resultado)
                                    data_gale = get_gale()
                                    time.sleep(0.3 * 60)
                                    break
        elif resultado == 'error':
            print('    Erro na operacao ', valor_entrada, ' resultado ', resultado)
    time.sleep(0.3 * 60)
