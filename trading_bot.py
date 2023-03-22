import os
import alpaca_trade_api as tradeapi
import pandas as pd


# Set your API keys
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY') or 'PKZPW7UYTUK9DM0Q0R4S'
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY') or 'ScJSkvQm5PVJPUQH4NBcES8I2HWmH5NxwQV2k8gu'


# Connect to the Alpaca API
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, base_url='https://paper-api.alpaca.markets', api_version='v2')



def calculate_sma(symbol, timeframe, period):
    end_date = pd.Timestamp.now(tz="America/New_York").floor('1D')
    start_date = end_date - pd.Timedelta(days=period * 2)
    try:
        barset = api.get_bars(
            symbol,
            tradeapi.TimeFrame.Day,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            limit=period,
            adjustment='raw',
        ).df
        return barset['close'].rolling(window=period).mean().iloc[-1]
    except KeyError:
        return None



def moving_average_crossover(symbol, short_period, long_period):
    short_sma = calculate_sma(symbol, tradeapi.TimeFrame.Day, short_period)
    long_sma = calculate_sma(symbol, tradeapi.TimeFrame.Day, long_period)

    print(f"{symbol} {short_period}-day SMA: {short_sma}")
    print(f"{symbol} {long_period}-day SMA: {long_sma}")

    if short_sma is None or long_sma is None:
        print(f"No data for {symbol}")
        return False

    return short_sma > long_sma




def liquidate_positions(api, symbol):
    try:
        position = api.get_position(symbol)
        if float(position.unrealized_plpc) < -0.05:
            api.submit_order(
                symbol=symbol,
                qty=position.qty,
                side='sell',
                type='stop',
                time_in_force='gtc',
                stop_loss=position.current_price * 0.95
            )
            print(f"Stop-loss order for {symbol} submitted")
    except Exception as e:
        print(f"Error liquidating positions for {symbol}: {e}")






def execute_trading_strategy():
    symbols = ['AAPL', 'GOOGL', 'AMZN', 'FB', 'TSLA', 'MSFT', 'NVDA', 'JPM', 'BRK.B', 'V', 'JNJ', 'PG', 'KO', 'DIS', 'NFLX', 'ORCL', 'IBM', 'XOM']
    short_period = 50
    long_period = 200
    position_size = 1

    for symbol in symbols:
        if moving_average_crossover(symbol, short_period, long_period):
            # Check if we already have a position
            position = None
            try:
                position = api.get_position(symbol)
            except Exception as e:
                print(f"No position found: {e}")

            # If we don't have a position, submit a buy order
            if position is None:
                print(f"Buying {position_size} shares of {symbol}")
                api.submit_order(
                    symbol=symbol,
                    qty=position_size,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
            else:
                print(f"Already holding {symbol}")
        else:
            print(f"No trade signal for {symbol}")
        # Liquidate positions if needed
        liquidate_positions(api, symbol)

if __name__ == '__main__':
    execute_trading_strategy()
