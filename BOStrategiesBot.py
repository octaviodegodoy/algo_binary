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
martingale = int(12)  # int(input(' Indique a quantia de martingales: '))
martingale += 1
capital_inicial = float(20000.0)

meta_diaria_ganho = float(2/100)*capital_inicial
meta_diaria_risco = float(3/100)*capital_inicial

stop_loss = meta_diaria_risco # float(input(' Indique o valor de Stop Loss: '))
stop_gain = meta_diaria_ganho  # float(input(' Indique o valor de Stop Gain: '))

amount_by_payout = {'0.74': '0.99', '0.75': '0.97', '0.76': '0.96', '0.77': '0.94', '0.78': '0.93', '0.79': '0.91',
                    '0.80': '0.90', '0.81': '0.88', '0.82': '0.87', '0.83': '0.85', '0.84': '0.84', '0.85': '0.83',
                    '0.86': '0.82', '0.87': '0.80', '0.88': '0.79', '0.89': '0.78', '0.90': '0.77', '0.91': '0.76',
                    '0.92': '0.75', '0.93': '0.74', '0.94': '0.73', '0.95': '0.72', '0.96': '0.71', '0.97': '0.70',
                    '0.98': '0.69', '0.99': '0.68', '100': '0.67'}


valor_entrada = get_initial_amount(par, amount_by_payout)

perda_acumulada = 0
lucro = 0
valor_soros = 0
lucro = 0
win_count = 0
while True:
    minutos = 1
    entrar = remaining_seconds(minutos)

    # if entrar < 15:
    if True:
        print('\n\nIniciando operação!')
        print('Verificando cores..', end='')
        # direcao = mhi_strategy(par)
        direcao = 'call'

        if direcao:
            print('Entrando com :', direcao)

            status, valor = entradas(par, valor_soros + valor_entrada, direcao, operacao)
            lucro += valor

            if 0 < perda_acumulada < valor:
                valor_entrada = get_initial_amount(par, amount_by_payout)
                continue

            if valor < 0 and win_count == 0:
                valor_entrada = 0
                perda_acumulada += abs(valor)
                valor_soros = float(perda_acumulada) / 2
            elif valor < 0 and win_count == 1:
                valor_entrada = 0
                perda_acumulada = abs(lucro)
                valor_soros = float(perda_acumulada) / 2
                win_count = 0
            elif valor > 0 and win_count == 0:
                win_count += 1
                valor_entrada += round(valor_soros + valor, 2)
                valor_soros = 0
            elif valor > 0 and win_count > 0:
                valor_entrada = get_initial_amount(par, amount_by_payout)
                valor_soros = 0
                continue

            stop(lucro, stop_gain, stop_loss)
            capital_inicial += lucro
            # time.sleep(minutos*60)
            """
            for i in range(martingale):
                print('Resultado operação: ', end='')
                print('WIN /' if valor > 0 else 'LOSS /', round(valor, 2), '/', round(lucro, 2),
                      ('/ ' + str(i) + ' GALE' if i > 0 else ''), ' par ', par, ' id da operacão ', id)

                # valor_entrada = Martingale(valor_entrada, payout)
                valor_entrada = soros_gale(valor, payout, )
                print("Novo valor entrada sorosgale ", valor_entrada, ' PAR ', par)

                stop(lucro, stop_gain, stop_loss)

                    if valor > 0:
                        break
                    elif valor < 0:
                        time.sleep(300)

                else:
                    print('\nERRO AO REALIZAR OPERAÇÃO\n\n')
            """
