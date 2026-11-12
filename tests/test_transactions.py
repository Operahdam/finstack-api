
import uuid
from decimal import Decimal


def create_wallet(client, auth_headers, currency="NGN"):
    response = client.post(
        "/wallets",
        json={"currency": currency},
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def credit(client, wallet_id, amount, auth_headers, key="credit-001"):
    headers = {
        **auth_headers,
        "Idempotency-Key": key,
    }

    return client.post(
        f"/transactions/wallets/{wallet_id}/credit",
        json={"amount": str(amount)},
        headers=headers,
    )


def debit(client, wallet_id, amount, auth_headers, key="debit-001"):
    headers = {
        **auth_headers,
        "Idempotency-Key": key,
    }

    return client.post(
        f"/transactions/wallets/{wallet_id}/debit",
        json={"amount": str(amount)},
        headers=headers,
    )


def balance(client, wallet_id, auth_headers):
    response = client.get(
        f"/wallets/{wallet_id}/balance",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    return Decimal(response.json()["balance"])


def test_credit_wallet(client, auth_headers):
    wallet_id = create_wallet(client, auth_headers)

    response = credit(
        client, wallet_id, "5000.00", auth_headers
    )

    assert response.status_code == 200
    assert response.json()["transaction_type"] == "CREDIT"
    assert balance(client, wallet_id, auth_headers) == Decimal("5000.00")


def test_debit_wallet(client, auth_headers):
    wallet_id = create_wallet(client, auth_headers)

    credit(client, wallet_id, "5000.00", auth_headers)
    response = debit(client, wallet_id, "1500.00", auth_headers)

    assert response.status_code == 200
    assert balance(client, wallet_id, auth_headers) == Decimal("3500.00")


def test_insufficient_balance(client, auth_headers):
    wallet_id = create_wallet(client, auth_headers)

    response = debit(client, wallet_id, "1000.00", auth_headers)

    assert response.status_code == 400
    assert balance(client, wallet_id, auth_headers) == Decimal("0.00")


def test_transfer_funds(client, auth_headers):
    source = create_wallet(client, auth_headers)
    destination = create_wallet(client, auth_headers)

    credit(client, source, "5000.00", auth_headers)

    response = client.post(
        "/transactions/transfer",
        params={"source_wallet_id": source},
        json={
            "amount": "2000.00",
            "destination_wallet_id": destination,
        },
        headers={
            **auth_headers,
            "Idempotency-Key": "transfer-001",
        },
    )

    assert response.status_code == 200
    assert response.json()["transaction_type"] == "TRANSFER"
    assert balance(client, source, auth_headers) == Decimal("3000.00")
    assert balance(client, destination, auth_headers) == Decimal("2000.00")


def test_transfer_to_same_wallet(client, auth_headers):
    wallet_id = create_wallet(client, auth_headers)

    response = client.post(
        "/transactions/transfer",
        params={"source_wallet_id": wallet_id},
        json={
            "amount": "100.00",
            "destination_wallet_id": wallet_id,
        },
        headers={
            **auth_headers,
            "Idempotency-Key": "transfer-same",
        },
    )

    assert response.status_code == 400


def test_credit_nonexistent_wallet(client, auth_headers):
    response = credit(
        client, uuid.uuid4(), "1000.00", auth_headers
    )

    assert response.status_code == 404


def test_idempotency_prevents_duplicate_credit(client, auth_headers):
    wallet_id = create_wallet(client, auth_headers)

    first = credit(
        client, wallet_id, "1000.00", auth_headers, "duplicate-key"
    )
    second = credit(
        client, wallet_id, "1000.00", auth_headers, "duplicate-key"
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json()["id"] == second.json()["id"]
    assert balance(client, wallet_id, auth_headers) == Decimal("1000.00")


def test_idempotency_rejects_different_request(client, auth_headers):
    wallet_id = create_wallet(client, auth_headers)

    credit(
        client, wallet_id, "1000.00", auth_headers, "reused-key"
    )

    response = credit(
        client, wallet_id, "2000.00", auth_headers, "reused-key"
    )

    assert response.status_code == 409
    assert balance(client, wallet_id, auth_headers) == Decimal("1000.00")


def test_transaction_history(client, auth_headers):
    wallet_id = create_wallet(client, auth_headers)

    credit(client, wallet_id, "1000.00", auth_headers, "history-001")
    credit(client, wallet_id, "500.00", auth_headers, "history-002")

    response = client.get(
        f"/transactions/wallets/{wallet_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["transactions"]) == 2


def test_transaction_pagination(client, auth_headers):
    wallet_id = create_wallet(client, auth_headers)

    for i in range(3):
        credit(
            client,
            wallet_id,
            "100.00",
            auth_headers,
            f"pagination-{i}",
        )

    response = client.get(
        f"/transactions/wallets/{wallet_id}",
        params={"skip": 0, "limit": 2},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()["transactions"]) == 2
    assert response.json()["total"] == 3


def test_multi_currency_credit_and_debit(client, auth_headers):
    for currency in ["USD", "GBP", "EUR"]:
        wallet_id = create_wallet(
            client,
            auth_headers,
            currency,
        )

        credit_response = credit(
            client,
            wallet_id,
            "100.00",
            auth_headers,
            f"{currency}-credit",
        )

        assert credit_response.status_code == 200
        assert credit_response.json()["currency"] == currency

        debit_response = debit(
            client,
            wallet_id,
            "25.00",
            auth_headers,
            f"{currency}-debit",
        )

        assert debit_response.status_code == 200
        assert debit_response.json()["currency"] == currency

        assert balance(
            client,
            wallet_id,
            auth_headers,
        ) == Decimal("75.00")


def test_transfer_between_different_currencies_rejected(
    client,
    auth_headers,
):
    source = create_wallet(client, auth_headers, "USD")
    destination = create_wallet(client, auth_headers, "GBP")

    credit_response = credit(
        client,
        source,
        "100.00",
        auth_headers,
        "currency-transfer-credit",
    )

    assert credit_response.status_code == 200

    response = client.post(
        "/transactions/transfer",
        params={"source_wallet_id": source},
        json={
            "amount": "50.00",
            "destination_wallet_id": destination,
        },
        headers={
            **auth_headers,
            "Idempotency-Key": "currency-mismatch-transfer",
        },
    )

    assert response.status_code == 400

    assert balance(client, source, auth_headers) == Decimal("100.00")
    assert balance(client, destination, auth_headers) == Decimal("0.00")
