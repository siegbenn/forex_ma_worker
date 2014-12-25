from globals import Globals
import datetime
from forex_moving_average_functions import get_account
from forex_moving_average_functions import save_account

# Initialize variables.
account_id = Globals.account
token = Globals.token

# Get current accout information.
account = get_account(account_id, token)

# Get current timestamp.
timestamp = datetime.datetime.now().isoformat()

# Create save the account info to DynamoDB.
save_account(account.account_id, timestamp, account.margin_used, account.margin_available, account.unrealized_pl, account.realized_pl, account.margin_rate, account.open_trades, account.open_orders, account.balance)
