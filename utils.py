from datetime import datetime, timedelta


# utils.py
def normalize_result(value):
    val = str(value).strip().lower() if value else ''
    if val in ['pass', 'fail']:
        return val.capitalize()
    elif val in ['n/a', 'na', 'not applicable', '']:
        return 'N/A'
    return 'N/A'
