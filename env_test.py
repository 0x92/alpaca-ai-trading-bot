from app.config import load_env

if __name__ == '__main__':
    env = load_env()
    print('ALPACA_API_KEY=', env.get('ALPACA_API_KEY'))
