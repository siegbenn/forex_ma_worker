import time
import boto.sqs
from boto.sqs.message import Message
from forex_moving_average_functions import get_position
from forex_moving_average_functions import delete_position
from forex_moving_average_functions import create_order

account_id = 6915436
token = '288b00b15a621d41699d496e287d1982-898404c2a1ffe97c68ef6d97e95eeb0f'

# Create connection to SQS queue.
conn = boto.sqs.connect_to_region('us-east-1')
queue = conn.get_queue('forex_moving_average_orders')
messages = True

while messages == True:
	rs = queue.get_messages(message_attributes=['pair', 'units', 'side'])
	if len(rs) == 1:
		m = rs[0]
		pair = m.message_attributes['pair']['string_value']
		units = int(m.message_attributes['units']['string_value'])
		side = m.message_attributes['side']['string_value']

		position = get_position(pair, account_id, token)

		current_position = position.pair
		current_side = position.side
		current_units = int(position.units)

		if current_side == side and current_units == units:
			print "don't make a trade"
			queue.delete_message(m)

		else:
			delete_position(pair, account_id, token)
			time.sleep(0.5)
			create_order(pair, account_id, token, side, units)
			queue.delete_message(m)

			print 'make a trade'


	else:
		messages = False

	time.sleep(0.5)
	
print "Done processing queue"