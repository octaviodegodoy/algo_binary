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
import math


def get_all_opened_assets(iqoapi):
    return iqoapi.get_all_open_time()


def is_asset_open(asset, all_opened_assets, mode='turbo'):
    return all_opened_assets[mode][asset]["open"]


def get_digital_profit(iqoapi, active, expiration):
    iqoapi.subscribe_strike_list(active, expiration)
    payout = iqoapi.get_digital_current_profit(active, expiration)
    while not payout:
        time.sleep(0.1)
        payout = iqoapi.get_digital_current_profit(active, expiration)
    iqoapi.unsubscribe_strike_list(active, expiration)
    return {'digital': math.floor(payout) / 100}


def get_all_profits(iqoapi):
    return iqoapi.get_all_profit()


def most_profit_mode(iqoapi, active, expiration, min_payout):
    _mpm = ['digital', False]

    all_opened_assets = get_all_opened_assets(iqoapi)
    opened = dict()
    for mode in ['turbo', 'digital']:
        opened[mode] = is_asset_open(active, all_opened_assets, mode)
    if opened['turbo'] or opened['digital']:
        profits = get_all_profits(iqoapi)
        if opened['digital']:
            if active in profits:
                profits[active].update(get_digital_profit(iqoapi, active, expiration))
            else:
                profits[active] = get_digital_profit(iqoapi, active, expiration)
        priority_mode_list = []
        for k, v in opened.items():
            if v:
                priority_mode_list.append([k, profits[active][k]])
        priority_mode_list = sorted(priority_mode_list, key=lambda x: x[1], reverse=True)
        if priority_mode_list:
            mode, best_payout = priority_mode_list[0]
            if best_payout >= min_payout:
                if mode == 'turbo':
                    _mpm[0], _mpm[1] = 'turbo', True
                else:
                    _mpm[0], _mpm[1] = 'digital', True
            else:
                # print(str(datetime.now()), "The payout for " + active + " is below " + str(float(best_payout) * 100) + "%")
                _mpm[0], _mpm[1] = 'payout', False
        else:
            # print(str(datetime.now()), active, "- Something went wrong. No items in your priority list :(")
            _mpm[0], _mpm[1] = 'error', False
    else:
        # print(str(datetime.now()), active + " is closed now. :(")
        _mpm[0], _mpm[1] = 'closed', False

    return _mpm[0], _mpm[1]


def stop(lucro, gain, loss):
    if lucro <= float('-' + str(abs(loss))):
        print('Stop Loss batido!')
        sys.exit()

    if lucro >= float(abs(gain)):
        print('Stop Gain Batido!')
        sys.exit()


def soros_gale(perda, payout):
    perda = float(abs(perda))
    perda += perda / float(1 + payout)
    entrada = round(perda, 2)
    return entrada


def martingale(valor, payout):
    lucro_esperado = valor * payout
    perda = float(valor)

    while True:
        if round(valor * payout, 2) > round(abs(perda) + lucro_esperado, 2):
            return round(valor, 2)
        valor += 0.01


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


def VerificaVelas(dir):
    velas = API.get_candles(par, 60, 6, time.time())

    velas[0] = 'g' if velas[0]['open'] < velas[0]['close'] else 'r' if velas[0]['open'] > velas[0]['close'] else 'd'
    velas[1] = 'g' if velas[1]['open'] < velas[1]['close'] else 'r' if velas[1]['open'] > velas[1]['close'] else 'd'
    velas[2] = 'g' if velas[2]['open'] < velas[2]['close'] else 'r' if velas[2]['open'] > velas[2]['close'] else 'd'
    velas[3] = 'g' if velas[3]['open'] < velas[3]['close'] else 'r' if velas[3]['open'] > velas[3]['close'] else 'd'
    velas[4] = 'g' if velas[4]['open'] < velas[4]['close'] else 'r' if velas[4]['open'] > velas[4]['close'] else 'd'
    velas[5] = 'g' if velas[5]['open'] < velas[5]['close'] else 'r' if velas[5]['open'] > velas[5]['close'] else 'd'

    cores = velas[0] + ' ' + velas[1] + ' ' + velas[2] + ' ' + velas[3] + ' ' + velas[4] + ' ' + velas[5]
    # print(cores)
    # print('Velas verdes ', cores.count('g'))
    # print('Velas vermelhas ', cores.count('r'))
    direction = dir
    color_candles = 3
    green_count = cores.count('g')
    red_count = cores.count('r')
    opera = False
    if green_count < color_candles:
        direction = 'call'
        opera = True
    if red_count < color_candles:
        direction = 'put'
        opera = True
    return opera, direction


print('''
	     Simples MHI BOT
	  youtube.com/c/IQCoding
 ------------------------------------
''')

API = IQ_Option('login', 'senha')
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

par = 'EURUSD-OTC'  # input(' Indique uma paridade para operar: ').upper()
valor_entrada = float(5.0)  # float(input(' Indique um valor para entrar: '))
valor_entrada_b = float(valor_entrada)

martingale = int(12)  # int(input(' Indique a quantia de martingales: '))
martingale += 1

stop_loss = float(1100.0)  # float(input(' Indique o valor de Stop Loss: '))
stop_gain = float(700.0)  # float(input(' Indique o valor de Stop Gain: '))

lucro = 0
payout = payout(par)

while True:
    minutos = float(((datetime.now()).strftime('%M.%S'))[1:])
    entrar = True if (minutos >= 4.58 and minutos <= 5) or minutos >= 9.58 else False
    # print('Hora de entrar?',entrar,'/ Minutos:',minutos)

    if entrar:
        print('\n\nIniciando operação!')
        dir = False
        print('Verificando cores..', end='')
        velas = API.get_candles(par, 60, 6, time.time())

        velas[0] = 'g' if velas[0]['open'] < velas[0]['close'] else 'r' if velas[0]['open'] > velas[0]['close'] else 'd'
        velas[1] = 'g' if velas[1]['open'] < velas[1]['close'] else 'r' if velas[1]['open'] > velas[1]['close'] else 'd'
        velas[2] = 'g' if velas[2]['open'] < velas[2]['close'] else 'r' if velas[2]['open'] > velas[2]['close'] else 'd'
        velas[3] = 'g' if velas[3]['open'] < velas[3]['close'] else 'r' if velas[3]['open'] > velas[3]['close'] else 'd'
        velas[4] = 'g' if velas[4]['open'] < velas[4]['close'] else 'r' if velas[4]['open'] > velas[4]['close'] else 'd'
        velas[5] = 'g' if velas[5]['open'] < velas[5]['close'] else 'r' if velas[5]['open'] > velas[5]['close'] else 'd'

        cores = velas[0] + ' ' + velas[1] + ' ' + velas[2] + ' ' + velas[3] + ' ' + velas[4] + ' ' + velas[5]
        print(cores)
        print('Velas verdes ', cores.count('g'))
        print('Velas vermelhas ', cores.count('r'))
        if (cores.count('g') + cores.count('r')) == 6:
            if cores.count('g') < 3: dir = ('call' if tipo_mhi == 1 else 'put')
            if cores.count('r') < 3: dir = ('put' if tipo_mhi == 1 else 'call')

        if dir:
            print('Direção:', dir)

            valor_entrada = valor_entrada_b
            perda_acumulada = 0
            for i in range(martingale):

                if i > 0:
                    while True:
                        opera, dir = VerificaVelas(dir)
                        if opera:
                            status, id = API.buy_digital_spot(par, valor_entrada, dir, 1) if operacao == 1 else API.buy(
                                valor_entrada, par, dir, 1)
                            break
                elif i == 0:
                    status, id = API.buy_digital_spot(par, valor_entrada, dir, 1) if operacao == 1 else API.buy(
                        valor_entrada, par,
                        dir, 1)

                if status:
                    while True:
                        try:
                            status, valor = API.check_win_digital_v2(id) if operacao == 1 else API.check_win_v3(id)
                        except:
                            status = True
                            valor = 0

                        if status:
                            valor = valor if valor > 0 else float('-' + str(abs(valor_entrada)))
                            lucro += round(valor, 2)

                            print('Resultado operação: ', end='')
                            print('WIN /' if valor > 0 else 'LOSS /', round(valor, 2), '/', round(lucro, 2),
                                  ('/ ' + str(i) + ' GALE' if i > 0 else ''), ' par ', par, ' id da operacão ', id)

                            # valor_entrada = Martingale(valor_entrada, payout)
                            valor_entrada = soros_gale(valor, payout)
                            print("Novo valor entrada sorosgale ", valor_entrada, ' PAR ', par)

                            stop(lucro, stop_gain, stop_loss)

                            break

                    if valor > 0:
                        break
                    elif valor < 0:
                        time.sleep(300)

                else:
                    print('\nERRO AO REALIZAR OPERAÇÃO\n\n')

    time.sleep(0.5)
