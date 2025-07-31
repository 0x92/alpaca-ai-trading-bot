from app.research_engine import get_research

if __name__ == "__main__":
    data = get_research("AAPL")
    print(data)
