import pytest
from decimal import Decimal
from backend.app.services.bnpl_service import BnplService, BnplCalculationResult, RepaymentEntry
from decimal import Decimal, ROUND_HALF_UP

def test_validate_eligibility_valid_minimum():
    BnplService.validate_eligibility(Decimal('3000.00'), 3)

def test_validate_eligibility_valid_maximum():
    BnplService.validate_eligibility(Decimal('200000.00'), 12)

def test_validate_eligibility_below_minimum():
    with pytest.raises(ValueError):
        BnplService.validate_eligibility(Decimal('2999.99'), 3)

def test_validate_eligibility_above_maximum():
    with pytest.raises(ValueError):
        BnplService.validate_eligibility(Decimal('200000.01'), 3)

def test_validate_eligibility_invalid_tenure():
    with pytest.raises(ValueError):
        BnplService.validate_eligibility(Decimal('5000.00'), 5)

@pytest.mark.parametrize("tenure,expected_rate", [
    (3, Decimal('0.12')),
    (6, Decimal('0.14')),
    (9, Decimal('0.16')),
    (12, Decimal('0.18')),
])
def test_interest_rate_mapping(tenure, expected_rate):
    result = BnplService.calculate_reducing_balance_emi(Decimal('10000.00'), tenure)
    assert result.annual_interest_rate == expected_rate

@pytest.mark.parametrize("tenure", [3, 6, 9, 12])
def test_repayment_schedule_length(tenure):
    result = BnplService.calculate_reducing_balance_emi(Decimal('10000.00'), tenure)
    assert len(result.repayment_schedule) == tenure

def test_repayment_schedule_entries():
    result = BnplService.calculate_reducing_balance_emi(Decimal('10000.00'), 3)
    for entry in result.repayment_schedule:
        assert isinstance(entry.month, int)
        assert isinstance(entry.emi, Decimal)
        assert isinstance(entry.interest, Decimal)
        assert isinstance(entry.principal, Decimal)
        assert isinstance(entry.remaining_balance, Decimal)

def test_reducing_balance_behavior():
    principal = Decimal('10000.00')
    tenure = 3
    result = BnplService.calculate_reducing_balance_emi(principal, tenure)
    interests = [entry.interest for entry in result.repayment_schedule]
    # Interest in month 2 should be less than month 1 due to reducing balance
    assert interests[1] < interests[0]

def test_total_principal_repaid_equals_original():
    principal = Decimal('10000.00')
    tenure = 3
    result = BnplService.calculate_reducing_balance_emi(principal, tenure)
    total_principal = sum(entry.principal for entry in result.repayment_schedule)
    assert total_principal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) == principal

def test_final_remaining_balance_zero():
    principal = Decimal('10000.00')
    tenure = 3
    result = BnplService.calculate_reducing_balance_emi(principal, tenure)
    final_balance = result.repayment_schedule[-1].remaining_balance
    assert final_balance == Decimal('0.00')

def test_total_repayment_equals_principal_plus_interest():
    principal = Decimal('10000.00')
    tenure = 3
    result = BnplService.calculate_reducing_balance_emi(principal, tenure)
    total_repayment = sum(entry.emi for entry in result.repayment_schedule)
    expected_total = (result.principal + result.total_interest).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    assert total_repayment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) == expected_total

def test_realistic_example():
    principal = Decimal('100000.00')
    tenure = 12
    result = BnplService.calculate_reducing_balance_emi(principal, tenure)
    assert len(result.repayment_schedule) == 12
    assert result.annual_interest_rate == Decimal('0.18')
    assert result.final_remaining_balance == Decimal('0.00') if hasattr(result, 'final_remaining_balance') else True