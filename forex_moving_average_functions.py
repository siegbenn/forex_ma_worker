import requests
import json
import boto.dynamodb
import boto.sqs
import boto.ses
from boto.sqs.message import Message
from boto.dynamodb2.table import Table


# Object to hold each moving average tick.
class Moving_Average_Tick(object):

    def __init__( self, timestamp, pair, moving_average_close, close, sentiment ):
        self.timestamp = timestamp
        self.pair = pair
        self.moving_average_close = moving_average_close
        self.close = close
        self.sentiment = sentiment

# Object to hold account information.
class Account(object):

    def __init__( self, open_trades, open_orders, margin_available, balance ):
        self.open_trades = open_trades
        self.open_orders = open_orders
        self.margin_available = margin_available
        self.balance = balance

# Object to hold price tick.
class Tick(object):

    def __init__( self, timestamp, pair, bid, ask, status ):
        self.timestamp = timestamp
        self.pair = pair
        self.bid = bid
        self.ask = ask
        self.status = status

# Create a Moving_Average_Tick with pair, length and ganularity.
def create_moving_average_tick ( pair, length, granularity, token ):
	
	# Send request to oanda and check for 200 response status code.
	response = requests.get('https://api-fxpractice.oanda.com/v1/candles?instrument=' + pair + '&count=' + str(length) + '&candleFormat=bidask&granularity=' + granularity + '&dailyAlignment=0&alignmentTimezone=America%2FNew_York', headers = { 'Authorization': 'Bearer '+ token })
	status_code = response.status_code

	# ERROR CHECK: status_code.
	if status_code != 200:
		raise Exception('Request status code != 200.')

	# Convert the response to JSON and set variables used in moving average calculation.
	response_json = response.json()
	pair_candles = response_json['candles']
	bar_count = len(pair_candles)

	# ERROR CHECK: pair_candles.
	if bar_count != length:
		raise Exception('Request returned incorrect amount of bars.')

	# Calculate the moving average.
	bar_sum = 0
	for i in range(0,bar_count):
		bar_sum += (pair_candles[i]['closeBid'] + pair_candles[i]['closeAsk']) / 2

	# Set the Moving_Average_Tick variables.
	timestamp = pair_candles[bar_count-1]['time']
	moving_average_close = (bar_sum / bar_count)
	close = (pair_candles[bar_count-1]['closeBid'] + pair_candles[bar_count-1]['closeAsk']) / 2
	sentiment = 'BULL'
	if close < moving_average_close:
		sentiment = 'BEAR'
	
	# Create the Moving_Average_Tick
	moving_average_tick = Moving_Average_Tick(timestamp,pair,moving_average_close,close, sentiment)

	# Return the Moving_Average_Tick.
	return moving_average_tick


# Get a full list of tradeable instruments for account.
def get_instrument_list ( account, token ):

	# Send request to oanda and check for 200 response status code.
	response = requests.get('https://api-fxpractice.oanda.com/v1/instruments?accountId=' + str(account), headers = { 'Authorization': 'Bearer ' + token })
	status_code = response.status_code

	# ERROR CHECK: status_code.
	if status_code != 200:
		raise Exception('Request status code != 200.')

	# Convert the response to JSON and populate instrument list.
	response_json = response.json()
	instruments_json = response_json['instruments']
	instrument_count = len(instruments_json)
	instruments = []
	for i in range(0,instrument_count):
		instruments.append(instruments_json[i]['instrument'])

	# Return the list of instrument names.
	return instruments


def save_moving_average_tick ( pair, timestamp, moving_average_close, close, sentiment):
	
	# Create DynamoDB connection.
	conn = boto.dynamodb.connect_to_region('us-east-1')
	table = conn.get_table('forex_moving_average_ticks')

	# Create DynamoDB tick item.
	tick = table.new_item(
		hash_key = pair,
		range_key = timestamp,
		attrs = { 'close': close, 'moving_average_close': moving_average_close, 'sentiment': sentiment}
	)

	# Save DynamoDB item.
	tick.put()


def create_queue_order ( pair, timestamp, direction, units ):

	# Create connection to SQS queue.
	conn = boto.sqs.connect_to_region('us-east-1')
	queue = conn.get_queue('forex_moving_average_orders')

	# Set queue message.
	message = Message()
	message.set_body(timestamp + ': ' + pair + ' ' + direction +  ' ' + str(units) )

	# Set queue message attributes.
	message.message_attributes = {
		"pair": {
			"data_type": "String",
			"string_value": pair
		},
		"timestamp": {
			"data_type": "String",
			"string_value": timestamp
		},
		"direction": {
			"data_type": "String",
			"string_value": direction
		},
		"units": {
			"data_type": "Number",
			"string_value": str(units)
		}
	}

	# Write message to queue.
	queue.write(message)


def get_moving_average_tick ( pair ):

	# Set the DynamoDB table.
	table = Table('forex_moving_average_ticks')

	# Query for latest moving_average_tick.
	ticks = table.query_2(
		pair__eq = 'EUR_USD',
		reverse = True,
		limit = 1
	)

	# Initialize Moving_Average_Tick variables.
	timestamp = ""
	pair = ""
	moving_average_close = 0
	close = 0
	sentiment = ""

	# Set the Moving_Average_Tick variables.
	for tick in ticks:
		timestamp = tick['timestamp']
		pair = tick['pair']
		moving_average_close = tick['moving_average_close']
		close = tick['moving_average_close']
		sentiment = tick['bar_sum']

	# Set the Moving_Average_Tick.
	moving_average_tick = Moving_Average_Tick(timestamp,pair,moving_average_close,close, sentiment)

	# Return the Moving_Average_Tick.
	return moving_average_tick

def get_account_balance ( account, token ):
	
	# Send request to oanda and check for 200 response status code.
	response = requests.get('https://api-fxpractice.oanda.com/v1/accounts/' + str(account), headers = { 'Authorization': 'Bearer '+ token })
	status_code = response.status_code

	# ERROR CHECK: status_code.
	if status_code != 200:
		raise Exception('Request status code != 200.')

	# Convert the response to JSON and set account variables.
	response_json = response.json()
	open_trades = response_json['openTrades']
	open_orders = response_json['openOrders']
	margin_available = response_json ['marginAvail']
	balance = response_json['balance']

	# Set the Account.
	account = Account(open_trades,open_orders,margin_available,balance)

	# Return the Account.
	return account

def get_current_price ( pair, token ):

	# Send request to oanda and check for 200 response status code.
	response = requests.get('https://api-fxpractice.oanda.com/v1/prices?instruments=' + pair, headers = { 'Authorization': 'Bearer '+ token })
	status_code = response.status_code

	# ERROR CHECK: status_code.
	if status_code != 200:
		raise Exception('Request status code != 200.')

	# Convert the response to JSON and set tick variables.
	response_json = response.json()
	timestamp = response_json['prices'][0]['time']
	pair = response_json['prices'][0]['instrument']
	bid = response_json['prices'][0]['bid']
	ask = response_json['prices'][0]['ask']
	status = response_json['prices'][0]['status']

	# Set the Tick.
	tick = Tick(timestamp,pair,bid,ask,status)

	# Return the Tick.
	return tick

def send_email ( address, subject, message ):
	conn = boto.ses.connect_to_region('us-east-1')
	conn.send_email(
        'bennett.e.siegel@gmail.com',
        subject,
        message,
        [address]
    )