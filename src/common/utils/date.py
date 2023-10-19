import datetime


def is_valid_date(date_str):
    try:
        datetime.datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def is_business_day(date_str):
    if not is_valid_date(date_str):
        return False

    date_obj = datetime.datetime.strptime(date_str, "%d/%m/%Y")
    day_of_week = date_obj.weekday()

    return day_of_week < 5
