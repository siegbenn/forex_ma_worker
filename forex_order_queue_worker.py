from forex_moving_average_functions import get_moving_average_tick
from forex_moving_average_functions import get_account
from forex_moving_average_functions import get_instrument_list
from forex_moving_average_functions import get_current_price
from forex_moving_average_functions import create_queue_order
from forex_moving_average_functions import send_email

import time
import math

account_id = 6915436
token = '288b00b15a621d41699d496e287d1982-898404c2a1ffe97c68ef6d97e95eeb0f'
margin = 10

account = get_account(account_id,token)
balance = account.balance
instruments = get_instrument_list( account_id,token)
instrument_count = len(instruments)

# Loop through instruments.
for i in range(0,len(instruments)):
	instrument = instruments[i]
	base = instrument[:3]
	base_normal = base + '_USD'
	found = 0
	price = 0
	market_open = False

	for j in range(0,len(instruments)):
		if base_normal == instruments[j]:
			found = 1
	if found == 1:
		base_tick = get_current_price(base_normal,token)
		if base_tick.status != 'halted':
			market_open = True
		price = base_tick.bid
	elif found == 0 and base_normal != 'USD_USD':
		base_reverse = 'USD_' + base
		base_tick = get_current_price(base_reverse,token)
		if base_tick.status != 'halted':
			market_open = True
		price = 1 / base_tick.bid
	elif base_normal == 'USD_USD':
		base_tick = get_current_price('EUR_USD',token)
		price = 1
		if base_tick.status != 'halted':
			market_open = True
	
	units = int(math.floor((balance/instrument_count) * margin / price))

	moving_average_tick = get_moving_average_tick(instrument)
	
	direction = 'buy'
	sentiment = moving_average_tick.sentiment
	if sentiment == 'BEAR':
		direction = 'sell'

	create_queue_order(instrument, direction, units)
	time.sleep(0.5)

send_email('bennett.e.siegel@gmail.com', 'Forex Order Queue Worker', 'All have been orders queued.')
