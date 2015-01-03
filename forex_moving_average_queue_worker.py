from globals import Globals
from forex_moving_average_functions import get_moving_average_tick
from forex_moving_average_functions import get_account
from forex_moving_average_functions import get_instrument_list
from forex_moving_average_functions import get_current_price
from forex_moving_average_functions import create_queue_order
from forex_moving_average_functions import send_email
import time
import math

# Initialize variables.
account_id = Globals.account
token = Globals.token
margin = Globals.margin
market_open = False
subject = 'Forex Order Queue Worker'
body = "Order Queue\n\n"

# Get account details.
account = get_account(account_id,token)

# Set account balance.
balance = account.balance * 0.5
total = 0
count = 0
# Get a list of instruments and count (can be set to a custom list).
instruments = get_instrument_list( account_id,token)
instrument_count = len(instruments)

# Loop through instruments.
for i in range(0,len(instruments)):
	
	# Set instrument to the current instrument.
	instrument = instruments[i]

	# Parse out the base currency.
	base = instrument[:3]

	# Add _USD to the currency to get the base_normal pair.
	base_normal = base + '_USD'

	# Initialize price and found variables.
	found = 0
	price = 0
	
	# Check to see if the instrument is in the total instruments list (change to query if custom list).
	for j in range(0,len(instruments)):
		if base_normal == instruments[j]:
			found = 1

	# If the base_normal instrument is in the instrument list:
	if found == 1:
		base_tick = get_current_price(base_normal,token)
		if base_tick.status == 'open':
			market_open = True
		price = base_tick.bid

	# If the base_normal instrument is not in the instrument list and not a USD pair:
	elif found == 0 and base_normal != 'USD_USD':

		# Reverse the pair order.
		base_reverse = 'USD_' + base
		base_tick = get_current_price(base_reverse,token)
		if base_tick.status != 'open':
			market_open = True
		price = 1 / base_tick.bid

	# If the base_normal instrument is a USD pair:
	elif base_normal == 'USD_USD':
		base_tick = get_current_price('EUR_USD',token)
		price = 1
		if base_tick.status != 'open':
			market_open = True
	
	# Get previous day's close.
	moving_average_tick = get_moving_average_tick(instrument)
	order_percent = float(moving_average_tick.order_percent)

	# Calculate the units based on margin, price, and base instrument pair price.
	print instrument
	dollar_amount = balance * order_percent
	dollar_margin = dollar_amount * margin
	print dollar_amount
	print dollar_margin
	total += dollar_margin

	units = int(math.floor(dollar_margin / price))

	print units
	if units != 0:
		count += 1
	# Set the order side based on the moving_average_tick sentiment.
	side = 'buy'
	sentiment = moving_average_tick.sentiment
	if sentiment == 'BEAR':
		side = 'sell'

	# Only queue orders if the market is open.
	if market_open == True and order_percent != 0:
		create_queue_order(instrument, side, units)
		body += instrument + '\n----------------\nSide: ' + side + '\nUnits: ' + str(units) + '\n\n' 
	time.sleep(0.5)

# Send confirmation email after enqueueing orders.
print total
print count
if market_open == True:
	body += 'All have been orders queued.'
	send_email('bennett.e.siegel@gmail.com', subject, body)
else:
	body += 'Market closed.'
	send_email('bennett.e.siegel@gmail.com', subject, body)
