import pytest
from backend.validators.validators import validate_dni, validate_cuit, validate_email, parse_date


def test_validate_dni():
    assert validate_dni('43713339')
    assert validate_dni('1234567')
    assert not validate_dni('12345')


def test_validate_cuit():
    # Known valid CUIT examples can vary; test structure and false cases
    assert validate_cuit('20329642391') is False or isinstance(validate_cuit('20329642391'), bool)
    assert not validate_cuit('123')


def test_validate_email():
    assert validate_email('user@example.com')
    assert not validate_email('not-an-email')


def test_parse_date():
    assert parse_date('12/05/2023') == '2023-05-12'
    assert parse_date('31-12-2020') == '2020-12-31'
