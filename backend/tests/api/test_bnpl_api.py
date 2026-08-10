import pytest
from decimal import Decimal
from fastapi import status
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_valid_bnpl_loan(client: AsyncClient, admin_token_headers):
    request_data = {
        "principal": "100000.00",
        "tenure": 12,
        "transaction_id": None
    }
    response = await client.post("/bnpl/loans", json=request_data, headers=admin_token_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["principal"] == "100000.00"
    assert data["tenure_months"] == 12
    assert data["annual_interest_rate"] == "0.18"
    assert data["monthly_emi"] == "9168.00"
    assert "repayment_schedule" in data
    assert len(data["repayment_schedule"]) == 12
    assert data["repayment_schedule"][-1]["remaining_balance"] == "0.00"

@pytest.mark.asyncio
async def test_create_bnpl_loan_below_minimum(client: AsyncClient, admin_token_headers):
    request_data = {
        "principal": "2999.99",
        "tenure": 3,
        "transaction_id": None
    }
    response = await client.post("/bnpl/loans", json=request_data, headers=admin_token_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_create_bnpl_loan_above_maximum(client: AsyncClient, admin_token_headers):
    request_data = {
        "principal": "200000.01",
        "tenure": 3,
        "transaction_id": None
    }
    response = await client.post("/bnpl/loans", json=request_data, headers=admin_token_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_create_bnpl_loan_invalid_tenure(client: AsyncClient, admin_token_headers):
    request_data = {
        "principal": "5000.00",
        "tenure": 5,
        "transaction_id": None
    }
    response = await client.post("/bnpl/loans", json=request_data, headers=admin_token_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_get_user_loans(client: AsyncClient, admin_token_headers):
    # Create a loan first
    request_data = {
        "principal": "3000.00",
        "tenure": 3,
        "transaction_id": None
    }
    create_response = await client.post("/bnpl/loans", json=request_data, headers=admin_token_headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    created_loan = create_response.json()

    # Get loans for the user
    get_response = await client.get("/bnpl/loans", headers=admin_token_headers)
    assert get_response.status_code == status.HTTP_200_OK
    loans = get_response.json()
    assert any(loan["id"] == created_loan["id"] for loan in loans)
