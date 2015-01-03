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
max_atr = -1
atr_mult_sum = 0

# Save the list of instruments.
instruments = get_instrument_list( account_id,token)


# Loop through instruments.
for i in range(0,len(instruments)):
	# Create the Moving_Average_Tick object.
	ma_tick = create_moving_average_tick(instruments[i],200,'D',token)
	atr = ma_tick.atr

	# Refresh the max_atr
	if atr > max_atr:
		max_atr = atr

	# Compate the atr to the max_atr to get the atr multiplier.
	atr_mult = max_atr/ ma_tick.atr

	# Only add atr_multiplier to the total if < 5.
	if atr_mult < 5:
		atr_mult_sum += atr_mult
	time.sleep(0.5)

# Loop through instruments.
for i in range(0,len(instruments)):

	# Create the Moving_Average_Tick object.
	ma_tick = create_moving_average_tick(instruments[i],200,'D',token)

	# Write the header on first iteration.
	if total == 0:
		body += ma_tick.timestamp + '\n\n'

	# Calculate the ATR multiplier %.
	atr_mult = max_atr/ ma_tick.atr
	
	# Calculate the normalized ATR multiplier %.
	if atr_mult < 5:
		order_percent = round(atr_mult/atr_mult_sum,4)
	else:
		order_percent = 0

	# Save the Moving_Average_Tick to DynamoDB.
	save_moving_average_tick(ma_tick.pair, ma_tick.timestamp, ma_tick.moving_average_close, ma_tick.close, ma_tick.sentiment, ma_tick.atr, order_percent)

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

