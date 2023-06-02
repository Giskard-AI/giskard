def format_number(value, n=3):
    if isinstance(value, float):
        if value > 1e6 or value < 1e-3:
            return f"{value:.{n}e}"
        else:
            return f"{value:.{3}f}"

    if isinstance(value, int) and abs(value) > 1e4:
        return f"{value:.{n}e}"

    return value
