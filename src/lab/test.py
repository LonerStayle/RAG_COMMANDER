import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from src.tools.Trade_Balance_tool import get_trade_balance

if __name__ == "__main__":
    result = get_trade_balance("서울")
    
    print(result)
