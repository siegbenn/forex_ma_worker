from globals import Globals
import time
from forex_moving_average_functions import get_instrument_list
from forex_moving_average_functions import create_moving_average_tick
from forex_moving_average_functions import save_moving_average_tick
from forex_moving_average_functions import send_email

# Initialize variables.
account_id = Globals.account
token = Globals.token
subject = 'Forex Moving Average Tick Worker'
body = 'All ticks have been saved.\n'
bear = 0
bull = 0
total = 0

# Save the list of instruments.
instruments = get_instrument_list( account_id,token)

# Loop through instruments.
for i in range(0,len(instruments)):

	# Create the Moving_Average_Tick object.
	ma_tick = create_moving_average_tick(instruments[i],200,'D',token)

	if total == 0:
		body += ma_tick.timestamp + '\n\n'

	# Save the Moving_Average_Tick to DynamoDB.
	save_moving_average_tick(ma_tick.pair, ma_tick.timestamp, ma_tick.moving_average_close, ma_tick.close, ma_tick.sentiment)

	# Count bearish or bullish.
	if ma_tick.sentiment == 'BEAR':
		bear += 1
		total += 1

	else:
		bull += 1
		total += 1

	# Append data to email body.
	body += ma_tick.pair + '\n----------------\nSentiment: ' + ma_tick.sentiment + '\nClose: ' + str(ma_tick.close) + '\nMA200: ' + str(ma_tick.moving_average_close) + '\n\n'

	# Sleep the loop for 1 second.
	time.sleep(0.5)

# Append totals to email body.
body += 'TOTALS\n----------------\n\n' + 'BEAR: ' + str(bear) + '\nBULL: ' + str(bull) + '\nTOTAL: ' + str(total)

# Send email.
send_email('bennett.e.siegel@gmail.com', subject, body)

