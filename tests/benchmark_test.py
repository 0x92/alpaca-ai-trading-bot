from app.benchmark import get_latest_benchmark_price, normalize_curve


def main():
    data = get_latest_benchmark_price()
    print('latest:', data)
    curve = normalize_curve([data])
    print('normalized:', curve)


if __name__ == '__main__':
    main()
