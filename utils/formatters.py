LOW_STOCK_THRESHOLD = 10


def format_currency(amount):
    if amount is None:
        return "৳0.00"
    return f"৳{float(amount):,.2f}"
