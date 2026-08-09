import pytest
from httpx import AsyncClient
from app.models import FraudReport
from app.schemas.fraud_report import FraudReportResponse
from decimal import Decimal
from datetime import date, datetime, timezone
import json


@pytest.mark.asyncio
async def test_fraud_report_api_authorized(client: AsyncClient, admin_token_headers, db_session):
    # Insert a test fraud report record
    report = FraudReport(
        report_date=date(2026, 8, 8),
        total_transactions=100,
        blocked_transactions=10,
        blocked_amount=Decimal("1234.56"),
        top_triggered_rules=[{"rule": "rule1", "count": 5}],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(report)
    await db_session.commit()

    response = await client.get("/api/fraud-reports/", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Check fields in the first report
    first_report = data[0]
    assert "id" in first_report
    assert first_report["report_date"] == "2026-08-08"
    assert first_report["total_transactions"] == 100
    assert first_report["blocked_transactions"] == 10
    assert first_report["blocked_amount"] == "1234.56"
    assert isinstance(first_report["top_triggered_rules"], list)
    assert "created_at" in first_report


@pytest.mark.asyncio
async def test_fraud_report_api_unauthorized(client: AsyncClient):
    response = await client.get("/api/fraud-reports/")
    assert response.status_code == 401 or response.status_code == 403


@pytest.mark.asyncio
async def test_fraud_report_api_empty(client: AsyncClient, admin_token_headers, db_session):
    # Ensure no fraud reports exist
    await db_session.execute("DELETE FROM fraud_reports")
    await db_session.commit()

    response = await client.get("/api/fraud-reports/", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data == []