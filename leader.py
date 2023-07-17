import asyncio
import json
import math
from datetime import datetime

import requests

import settings
from http_commands import get, post, patch
from terminal import Terminal

terminal: Terminal
event_loop = asyncio.Event()  # init async event
init_data = {}
host = settings.host
terminal_path = settings.terminal_path
exchange_id = settings.exchange_id


async def send_history_position(position_ticket, max_balance):
    url = settings.host + f'position/get/{settings.exchange_id}/{position_ticket}'
    response = await get(url)
    url = settings.host + f'option/get/{exchange_id}'
    options = (await get(url=url))[-1]
    if response:
        investment = response[0]['investment_size']
    else:
        investment = 0
    slippage_percent = options['deal_in_plus'] if options['deal_in_plus'] \
        else options['deal_in_minus']
    drawdown = (max_balance - (Terminal.get_account_balance() - investment)) / max_balance
    history_orders = Terminal.get_history_orders_for_ticket(int(position_ticket))
    deals_time = [deal.time_done for deal in history_orders]
    date_open = deals_time[0]
    date_close = deals_time[-1]
    # datetime.fromtimestamp(deal.time).strftime('%m/%d/%Y %H:%M:%S')
    deals_price = [deal.price_current for deal in history_orders]
    price_open = deals_price[0]
    price_close = deals_price[-1]
    change_percent = round(math.fabs(price_close - price_open) / price_open, 2)

    volumes = [deal.volume_initial for deal in history_orders]
    result_volume = 0
    for vol in volumes[1:]:
        result_volume = volumes[0] - vol
    volume_percent = (1 - result_volume / volumes[0]) * 100
    # print(volumes, volumes[1:])

    position = history_orders[0]
    if not position:
        return
    volume = history_orders[-1].volume_initial

    rates = Terminal.copy_rates_range(position.symbol, date_open - 1, date_close)
    if len(rates):
        price_max = max([_[2] for _ in rates])
        price_min = min([_[3] for _ in rates])
    else:
        price_min = price_max = 0
    history_deals = Terminal.get_history_deals_for_ticket(int(position_ticket))
    if history_deals:
        fee = history_deals[-1].fee
        swap = history_deals[-1].swap
    else:
        fee = swap = 0
    costs = fee + swap
    profits = [deal.profit for deal in history_deals]
    gross_pl = sum(profits)
    net_pl = gross_pl + costs
    balance = investment + net_pl

    current_positions = Terminal.get_positions()
    current_profit = 0
    for pos in current_positions:
        current_profit += pos.profit
    float_pl = Terminal.get_account_balance() - current_profit
    equity = Terminal.get_account_balance() + current_profit
    size = volume * Terminal.get_contract_size(position.symbol) * price_open
    bal_net = balance - net_pl
    lever = size / bal_net if bal_net else 0
    balance_percent = lever * 100
    if position.type == 0:  # BUY
        minimum = (price_min / price_open) * lever * 100 * -1
        maximum = (price_max / price_open) * lever * 100 * -1
    else:  # SELL
        minimum = (price_max / price_open) * lever * 100 * -1
        maximum = (price_min / price_open) * lever * 100 * -1

    data = {
        'ticket': position.ticket,  # Ticket
        'exchange': 'MT5',  # Exchange
        'user_id': '',  #
        'api_key': init_data['login'],  # API Key
        'secret_key': init_data['password'],  # Secret Key
        'account': str(exchange_id),  # Account
        'strategy': '',  #
        'investment': 0,  #
        'multiplicator': options['multiplier_value'],  # Multiplicator
        'stop_out': options['stop_value'],  # Stop out
        'symbol': position.symbol,  # Symbol
        'type': '',  #
        'position': '',  #
        'side': 'buy' if position.type == 0 else 'sell' if position.type == 1 else 'not buy or sell',  # Side
        'currency': '',  #
        'slippage_percent': slippage_percent,  # Slippage %
        'slippage_time': options['waiting_time'],  # Slippage time
        'size': size,  # Size
        'lots': volume,  # Lots
        'lever': lever,  # Lever
        'balance_percent': balance_percent,  # Balance %
        'volume_percent': volume_percent,  # Volume %
        'open_time': date_open,  # Open Time
        'open_price': price_open,  # Open Price
        'stop_loss': response[0]['sl'] if response else 0,  # history_orders[-1].sl,  # Stop loss
        'take_profit': response[0]['tp'] if response else 0,  # history_orders[-1].tp,  # Take profit
        'close_time': date_close,  # Close time
        'close_price': price_close,  # Close Price
        'change_percent': change_percent,  # Change_%
        'gross_p_l': gross_pl,  # Gross P&L
        'commision': fee,  # Fee
        'swap': swap,  # Swap
        'costs': costs,  # Costs
        'net_p_l': net_pl,  # Net P&L
        'roi': 0,  #
        'balance': balance,  # Balance
        'equity': equity,  # Equity
        'float_p_l': float_pl,  # Float P&L
        'duration': 0,  #
        'drawdown': drawdown,  # Drawdown
        'minimum': minimum,  # Minimum
        'maximum': maximum,  # Maximum
        'risk_reward': 0,  # `
        'roi_missed': 0,  # `
        'slip_percent': 0,  # `
        'slip_time': 0,  # `
        'magic': str(position.magic),  # Magic
        'comment': position.comment,  # Comment
    }
    print('history_position:\n', data)
    url = settings.host + 'position-history/post'
    await post(url, data=json.dumps(data))


def get_settings(exchange_idx):
    global init_data
    try:
        url = host + f'exchange/get/{exchange_idx}'
        init_data = requests.get(url=url).json()[-1]
        init_data['path'] = terminal_path
    except Exception as e:
        print(e)
        get_settings(exchange_idx)


async def send_position(position):
    url = host + 'position/post'
    data = {
        "exchange_pk": exchange_id,
        "ticket": position.ticket,
        "time": position.time,
        "time_update": position.time_update,
        "type": position.type,
        "magic": settings.MAGIC,
        "volume": position.volume,
        "price_open": position.price_open,
        "tp": position.tp,
        "sl": position.sl,
        "price_current": position.price_current,
        "symbol": position.symbol,
        "comment": position.comment,
        "profit": position.profit,
        "price_close": 0,
        "time_close": 0,
        "investment_size": init_data['investment_size'],
        "active": True
    }
    print(f'\t-- add position {data["ticket"]}')
    print(json.dumps(data))
    await post(url=url, data=json.dumps(data))


async def update_position(position):
    url = host + f'position/patch/{exchange_id}/{position.ticket}'
    data = {
        "time_update": position.time_update,
        "volume": position.volume,
        "tp": position.tp,
        "sl": position.sl,
        "profit": position.profit,
        "price_current": position.price_current,
        "comment": position.comment,
    }
    await patch(url=url, data=json.dumps(data))


async def disable_position(id_exchange, position_ticket):
    url = host + f'position/patch/{id_exchange}/{position_ticket}'
    data = {
        # "price_close": 0,
        # "time_close": 0,
        "active": False
    }
    print(f'\t-- disable position {position_ticket}')
    await patch(url=url, data=json.dumps(data))


async def get_db_positions(id_exchange):
    url = host + f'position/list/active/{id_exchange}'
    return await get(url=url)


async def send_trade_state(balance, equity):
    url = host + f'exchange/patch/{exchange_id}'
    data = {'balance': balance,
            'equity': equity,
            }
    await patch(url=url, data=json.dumps(data))


def send_currency():
    url = host + f'exchange/patch/{exchange_id}'
    data = {"currency": Terminal.get_account_currency()}
    requests.patch(url=url, data=json.dumps(data))


async def update_leader_info(sleep=settings.sleep_leader_update):
    while True:
        leader_balance = terminal.get_balance()
        leader_equity = terminal.get_equity()
        await send_trade_state(leader_balance, leader_equity)

        active_db_positions = await get_db_positions(exchange_id)
        active_db_tickets = [int(position['ticket']) for position in active_db_positions]
        terminal_positions = Terminal.get_positions(only_own=False)
        terminal_tickets = [position.ticket for position in terminal_positions]
        for position in active_db_positions:
            if int(position['ticket']) not in terminal_tickets:
                await disable_position(exchange_id, int(position['ticket']))
                await send_history_position(position['ticket'], leader_balance)
        for position in terminal_positions:
            if position.ticket not in active_db_tickets:
                await send_position(position)
            else:
                await update_position(position)

        print(
            f'{terminal.login} [{Terminal.get_account_currency()}] - {len(terminal_positions)} positions :',
            datetime.now().replace(), "- LEADER")
        await asyncio.sleep(sleep)


if __name__ == '__main__':
    get_settings(exchange_id)
    print(init_data)

    if not Terminal.is_init_data_valid(init_data):
        exit()
    terminal = Terminal(login=int(init_data['login']),
                        password=init_data['password'],
                        server=init_data['server'],
                        path=init_data['path'],
                        portable=True,
                        start_date=datetime.now())
    if not terminal.init_mt():
        print('Ошибка инициализации лидера'.encode('utf-8'), init_data)
        exit()

    send_currency()

    event_loop = asyncio.new_event_loop()
    event_loop.create_task(update_leader_info())
    event_loop.run_forever()
