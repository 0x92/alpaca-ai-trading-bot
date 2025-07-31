from app.diversification import calculate_correlation, diversification_score


def main():
    corr = calculate_correlation(["AAPL", "MSFT", "GOOG"], days=30)
    print("corr matrix", corr.to_dict())
    score = diversification_score(corr)
    print("score", score)


if __name__ == "__main__":
    main()
