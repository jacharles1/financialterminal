import requests
import plotext as plt
import time
from datetime import datetime, timedelta
import os
import shutil
import threading
import yfinance as yf

def fetch_kraken_data(pair, since):
    pair_mapping = {
        'BTCUSD': 'XXBTZUSD',
        'ETHUSD': 'XETHZUSD',
        'XRPUSD': 'XXRPZUSD',
        'LTCUSD': 'XLTCZUSD',
        'DOTUSD': 'DOTUSD',
        'ADAUSD': 'ADAUSD',
        'SOLUSD': 'SOLUSD',
        'MATICUSD': 'MATICUSD',
        'LINKUSD': 'LINKUSD',
        'UNIUSD': 'UNIUSD'
    }
    kraken_pair = pair_mapping.get(pair, pair)

    url = f"https://api.kraken.com/0/public/OHLC?pair={kraken_pair}&interval=1440&since={since}"
    headers = {'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    json_dict = response.json()
    
    result_key = list(json_dict['result'].keys())[0]
    ohlc_data = json_dict['result'][result_key]
    
    return [
        {'time': float(data[0]), 'price': float(data[4])}  # Using closing price
        for data in ohlc_data
    ]

def fetch_orderbook(pair):
    pair_mapping = {
        'BTCUSD': 'XXBTZUSD',
        'ETHUSD': 'XETHZUSD',
        'XRPUSD': 'XXRPZUSD',
        'LTCUSD': 'XLTCZUSD',
        'DOTUSD': 'DOTUSD',
        'ADAUSD': 'ADAUSD',
        'SOLUSD': 'SOLUSD',
        'MATICUSD': 'MATICUSD',
        'LINKUSD': 'LINKUSD',
        'UNIUSD': 'UNIUSD'
    }
    kraken_pair = pair_mapping.get(pair, pair)

    url = f"https://api.kraken.com/0/public/Depth?pair={kraken_pair}&count=5"
    response = requests.get(url)
    data = response.json()
    result = data['result']
    pair_name = list(result.keys())[0]
    return result[pair_name]

def format_number(number, max_length):
    """Format a number to fit within max_length characters."""
    str_num = f"{float(number):.8f}".rstrip('0').rstrip('.')
    if len(str_num) <= max_length:
        return str_num
    
    # If number is too long, use scientific notation
    return f"{float(number):.{max_length-6}e}"

def display_orderbook(pair, orderbook, max_width):
    lines = []
    lines.append(f"Orderbook for {pair}".rjust(max_width))
    lines.append("Bids:".rjust(max_width))
    for bid in orderbook['bids'][:5]:
        price = format_number(bid[0], 10)
        volume = format_number(bid[1], 10)
        line = f"P: {price}, V: {volume}"
        lines.append(f"\033[32m{line.rjust(max_width)}\033[0m")
    lines.append("Asks:".rjust(max_width))
    for ask in orderbook['asks'][:5]:
        price = format_number(ask[0], 10)
        volume = format_number(ask[1], 10)
        line = f"P: {price}, V: {volume}"
        lines.append(f"\033[31m{line.rjust(max_width)}\033[0m")
    return lines

def plot_trades_with_orderbook(pair, trades, orderbook):
    terminal_size = shutil.get_terminal_size()
    plt.clf()
    
    orderbook_width = 40
    plot_width = terminal_size.columns - orderbook_width
    plot_height = terminal_size.lines - 10
    
    plt.plotsize(plot_width, plot_height)
    
    prices = [trade['price'] for trade in trades]
    times = [trade['time'] for trade in trades]

    plt.theme('dark')
    plt.canvas_color('black')
    plt.axes_color('black')
    plt.ticks_color('white')

    plt.plot(times, prices, marker='braille', color='white')
    plt.title(f"{pair} Price Chart")
    plt.xlabel("Date")
    plt.ylabel("Price")
    
    # Add more dates to the x-axis
    num_dates = min(5, len(times))  # Use up to 5 dates, or less if fewer data points
    date_indices = [int(i * (len(times) - 1) / (num_dates - 1)) for i in range(num_dates)]
    plt.xticks([times[i] for i in date_indices], 
               [datetime.fromtimestamp(times[i]).strftime('%Y-%m-%d') for i in date_indices])
    
    y_min, y_max = min(prices), max(prices)
    y_range = y_max - y_min
    plt.ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)
    
    plt.frame(False)
    
    plot_string = plt.build()
    plot_lines = plot_string.split('\n')
    
    orderbook_lines = display_orderbook(pair, orderbook, orderbook_width)
    
    for i in range(max(len(plot_lines), len(orderbook_lines))):
        plot_line = plot_lines[i] if i < len(plot_lines) else ' ' * plot_width
        orderbook_line = orderbook_lines[i] if i < len(orderbook_lines) else ' ' * orderbook_width
        print(f"{plot_line}{orderbook_line}")

def update_display(pair, trades):
    thread = threading.current_thread()
    while getattr(thread, "do_run", True):
        orderbook = fetch_orderbook(pair)
        os.system('cls' if os.name == 'nt' else 'clear')
        plot_trades_with_orderbook(pair, trades, orderbook)
        time.sleep(5)  # Update every 5 seconds

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def search_ticker(query):
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if 'quotes' in data and data['quotes']:
        return data['quotes'][0]['symbol']
    return None

def fetch_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        'name': info.get('longName', 'Not found'),
        'price': info.get('currentPrice', 'Not found'),
        'market_cap': info.get('marketCap', 'N/A'),
        'shares_outstanding': info.get('sharesOutstanding', 'N/A'),
        'pe_ratio': info.get('trailingPE', 'N/A'),
        'dividend_yield': info.get('dividendYield', 'N/A'),
        '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
        '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
    }

def fetch_stock_history(ticker, period):
    stock = yf.Ticker(ticker)
    history = stock.history(period=period)
    return [
        {'time': time.timestamp(), 'price': price}
        for time, price in zip(history.index, history['Close'])
    ]

def plot_stock(ticker, trades, company_name, period):
    terminal_size = shutil.get_terminal_size()
    plt.clf()
    plt.plotsize(terminal_size.columns, terminal_size.lines - 5)  # Adjust for prompt space
    
    prices = [trade['price'] for trade in trades]
    times = [trade['time'] for trade in trades]

    plt.theme('dark')
    plt.canvas_color('black')
    plt.axes_color('black')
    plt.ticks_color('white')

    plt.plot(times, prices, marker='braille', color='white')
    plt.title(f"{company_name} Price Chart ({period})")
    plt.xlabel("Date")
    plt.ylabel("Price")
    
    # Add more dates to the x-axis
    num_dates = min(5, len(times))  # Use up to 5 dates, or less if fewer data points
    date_indices = [int(i * (len(times) - 1) / (num_dates - 1)) for i in range(num_dates)]
    plt.xticks([times[i] for i in date_indices], 
               [datetime.fromtimestamp(times[i]).strftime('%Y-%m-%d') for i in date_indices])
    
    y_min, y_max = min(prices), max(prices)
    y_range = y_max - y_min
    plt.ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)
    
    plt.frame(False)
    
    plt.show()

def get_period_choice():
    while True:
        choice = input("Choose timeline (d: 1 day, w: 1 week, m: 1 month, 1: 1 year, 5: 5 years): ").lower()
        if choice in ['d', 'w', 'm', '1', '5']:
            return {'d': '1d', 'w': '1wk', 'm': '1mo', '1': '1y', '5': '5y'}[choice]
        else:
            print("Invalid choice. Please try again.")

def crypto_main():
    while True:
        pairs = ['BTCUSD', 'ETHUSD', 'XRPUSD', 'LTCUSD', 'DOTUSD', 'ADAUSD', 'SOLUSD', 'MATICUSD', 'LINKUSD', 'UNIUSD']
        print("Select a cryptocurrency pair:")
        for i, pair in enumerate(pairs, 1):
            print(f"{i}. {pair}")
        print("Type 'q' to go back to the main menu")

        choice = input(f"Enter your choice (1-{len(pairs)} or 'q'): ").strip().upper()
        
        if choice == 'Q':
            print("Returning to main menu...")
            break

        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(pairs):
                selected_pair = pairs[choice_num - 1]
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(pairs)}.")
                continue
        except ValueError:
            print("Invalid input. Please enter a number or 'q'.")
            continue

        last_size = shutil.get_terminal_size()
        trades = None

        # Start the display update thread
        update_thread = None

        while True:
            current_size = shutil.get_terminal_size()
            
            if trades is None or current_size != last_size:
                clear_screen()
                print(f"Fetching data for {selected_pair}...")
                since = int((datetime.now() - timedelta(days=30)).timestamp())
                trades = fetch_kraken_data(selected_pair, since)
                last_size = current_size

                # Stop the previous update thread if it exists
                if update_thread and update_thread.is_alive():
                    update_thread.do_run = False
                    update_thread.join()

                # Start a new display update thread
                update_thread = threading.Thread(target=update_display, args=(selected_pair, trades))
                update_thread.do_run = True
                update_thread.start()

            user_input = input("Enter a new pair (e.g., BTCUSD), 'q' to go back to pair selection, or 'x' to exit: ").upper()
            if user_input == 'X':
                print("Exiting the program...")
                return  # Exit the entire crypto function
            elif user_input == 'Q':
                # Stop the update thread before going back to pair selection
                if update_thread and update_thread.is_alive():
                    update_thread.do_run = False
                    update_thread.join()
                break  # Go back to pair selection
            elif user_input in pairs:
                selected_pair = user_input
                trades = None  # Force data refresh
            else:
                print("Invalid input. Please try again.")

def stock_main():
    while True:
        query = input("Enter a company name or ticker symbol (or 'q' to quit): ").strip()
        if query.lower() == 'q':
            break

        ticker = search_ticker(query)
        if not ticker:
            print("Company or ticker not found. Please try again.")
            continue

        print(f"Fetching data for {ticker}...")
        stock_data = fetch_stock_data(ticker)
        print(f"Company Name: {stock_data['name']}")
        print(f"Stock Price: ${stock_data['price']:.2f}")
        print(f"Market Cap: ${stock_data['market_cap']:,}")
        print(f"Shares Outstanding: {stock_data['shares_outstanding']:,}")
        print(f"P/E Ratio: {stock_data['pe_ratio']:.2f}" if stock_data['pe_ratio'] != 'N/A' else "P/E Ratio: N/A")
        print(f"Dividend Yield: {stock_data['dividend_yield']:.2%}" if stock_data['dividend_yield'] != 'N/A' else "Dividend Yield: N/A")
        print(f"52 Week High: ${stock_data['52_week_high']:.2f}")
        print(f"52 Week Low: ${stock_data['52_week_low']:.2f}")
        print()

        while True:
            choice = input("Enter 'g' to view graph, 'n' for new ticker, or 'q' to quit: ").lower()
            if choice == 'q':
                return
            elif choice == 'n':
                break
            elif choice == 'g':
                period = get_period_choice()
                history = fetch_stock_history(ticker, period)
                plot_stock(ticker, history, stock_data['name'], period)

                user_input = input("Press 'r' to choose another timeline, any other key to continue, or 'q' to quit: ").lower()
                if user_input == 'q':
                    return
                elif user_input != 'r':
                    break
            else:
                print("Invalid input. Please try again.")

        clear_screen()

def main():
    while True:
        choice = input("Type 'S' for stocks, 'C' for crypto, or 'Q' to quit: ").upper()
        if choice == 'S':
            stock_main()
        elif choice == 'C':
            crypto_main()
        elif choice == 'Q':
            print("Exiting the program...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
