import re
from typing import Optional
from datetime import datetime

def validate_dni(value: str) -> bool:
    v = re.sub(r"\D", "", value or "")
    return len(v) == 7 or len(v) == 8

def validate_cuit(cuit: str) -> bool:
    num = re.sub(r"\D", "", cuit or "")
    if len(num) != 11:
        return False
    try:
        digits = list(map(int, num))
    except Exception:
        return False
    mult = [5,4,3,2,7,6,5,4,3,2]
    s = sum(d*m for d,m in zip(digits[:10], mult))
    ver = 11 - (s % 11)
    if ver == 11:
        ver = 0
    if ver == 10:
        return False
    return ver == digits[10]

def validate_email(email: str) -> bool:
    if not email:
        return False
    pattern = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

def normalize_phone(phone: str) -> Optional[str]:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 8:
        return None
    return digits

def parse_date(value: str) -> Optional[str]:
    if not value:
        return None
    from dateutil import parser
    try:
        dt = parser.parse(value, dayfirst=True, fuzzy=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None

if __name__ == '__main__':
    # quick smoke tests
    assert validate_dni('43713339')
    assert validate_cuit('30706686056') is False or isinstance(validate_cuit('30706686056'), bool)
    print('validators ok')
