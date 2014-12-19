import requests
import json
import time
import boto.dynamodb


class Moving_Average_Tick(object):

    def __init__(self, timestamp, pair, moving_average_close, close, sentiment):
        self.timestamp = timestamp
        self.pair = pair
        self.moving_average_close = moving_average_close
        self.close = close
        self.sentiment = sentiment


def calculate_moving_average ( pair, length, granularity ):
	
	# Send request to oanda and check for 200 response status code.
	response = requests.get('https://api-fxpractice.oanda.com/v1/candles?instrument='+pair+'&count='+str(length)+'&candleFormat=bidask&granularity='+granularity+'&dailyAlignment=0&alignmentTimezone=America%2FNew_York', headers={'Authorization': 'Bearer 288b00b15a621d41699d496e287d1982-898404c2a1ffe97c68ef6d97e95eeb0f'})
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
		bar_sum += ((pair_candles[i]['closeBid'] + pair_candles[i]['closeAsk']) / 2)

	# Set the Moving_Average_Tick variables.
	timestamp = pair_candles[bar_count-1]['time']
	moving_average_close = (bar_sum / bar_count)
	close = ((pair_candles[bar_count-1]['closeBid'] + pair_candles[bar_count-1]['closeAsk']) / 2)
	sentiment = 'BULL'
	if close < moving_average_close:
		sentiment = 'BEAR'
	
	# Create the Moving_Average_Tick
	moving_average_tick = Moving_Average_Tick(timestamp,pair,moving_average_close,close, sentiment)

	# Return the Moving_Average_Tick.
	return moving_average_tick

def get_instrument_list ( id, token ):

	# Send request to oanda and check for 200 response status code.
	response = requests.get('https://api-fxpractice.oanda.com/v1/instruments?accountId='+str(id), headers={'Authorization': 'Bearer '+token})
	status_code = response.status_code

	# ERROR CHECK: status_code.
	if status_code != 200:
		raise Exception('Request status code != 200.')

	# Convert the response to JSON and set variables used in moving average calculation.
	response_json = response.json()
	instruments_json = response_json['instruments']
	instrument_count = len(instruments_json)
	instruments = []
	for i in range(0,instrument_count):
		instruments.append(instruments_json[i]['instrument'])
	return instruments

instruments = get_instrument_list( 6915436,'288b00b15a621d41699d496e287d1982-898404c2a1ffe97c68ef6d97e95eeb0f')

bull = 0
bear = 0
for i in range(0,len(instruments)):
	ma_tick = calculate_moving_average(instruments[i],200,"D")
	print ma_tick.pair
	print ma_tick.timestamp
	print ma_tick.moving_average_close
	print ma_tick.close
	print ma_tick.sentiment
	if ma_tick.sentiment == 'BULL':
		bull += 1
	else:
		bear += 1
	conn = boto.dynamodb.connect_to_region('us-east-1')
	table = conn.get_table('forex_ma')
	item = table.new_item(
		hash_key = ma_tick.pair,
		range_key = ma_tick.timestamp,
		attrs = { 'close': ma_tick.close, 'moving_average_close': ma_tick.moving_average_close, 'sentiment': ma_tick.sentiment}
	)
	item.put()
	print ma_tick.pair + ": Saved to DynamoDB."
	time.sleep(1)
print "BEAR: " + str(bear)
print "BULL: " + str(bull)



