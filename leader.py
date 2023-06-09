import asyncio
import json
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
