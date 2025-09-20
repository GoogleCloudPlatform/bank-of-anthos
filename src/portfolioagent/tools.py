import time
import random


def read_boa_balances(user_id: str):
    """
    Placeholder tool to read Bank of Anthos balances.
    In a real scenario, this would make a gRPC call to the balancereader service.
    """
    print(f"TOOL: Reading balances for user {user_id}...")
    # Simulate network latency
    time.sleep(1)
    balance = round(random.uniform(500.0, 5000.0), 2)
    return {"status": "success", "balance": f"${balance}"}


def analyze_portfolio_risk(user_id: str, portfolio_assets: list):
    """
    Placeholder tool to analyze portfolio risk.
    In a real scenario, this would call a complex risk model.
    """
    print(f"TOOL: Analyzing risk for {user_id} with assets {portfolio_assets}...")
    # Simulate a longer-running task
    time.sleep(2)

    # Simulate a potential failure
    if random.random() < 0.2:  # 20% chance of failure
        print("TOOL: Risk analysis failed!")
        return {"status": "error", "message": "Failed to connect to risk model."}

    risk_score = round(random.uniform(0.1, 0.9), 2)
    return {"status": "success", "risk_score": risk_score}


def check_portfolio_compliance(portfolio_assets: dict, total_value: float):
    """
    Checks if a proposed portfolio meets defined budget and risk constraints.
    Returns a list of compliance violations, if any.
    """
    print(f"TOOL: Checking compliance for portfolio: {portfolio_assets}")
    violations = []

    # Rule 1: Minimum cash percentage
    min_cash_percent = 0.05  # 5%
    cash_value = portfolio_assets.get("CASH_USD", 0)
    if (cash_value / total_value) < min_cash_percent:
        violations.append(
            f"Cash holding is below the minimum {min_cash_percent*100}% threshold."
        )

    # Rule 2: Maximum single-asset concentration
    max_asset_percent = 0.40  # 40%
    for asset, value in portfolio_assets.items():
        if asset != "CASH_USD":
            if (value / total_value) > max_asset_percent:
                violations.append(
                    f"Asset '{asset}' exceeds the max concentration of {max_asset_percent*100}%."
                )

    if not violations:
        return {"status": "success", "compliant": True}
    else:
        return {"status": "success", "compliant": False, "violations": violations}


def execute_trade(user_id: str, trade_details: dict):
    """
    Placeholder tool for executing a trade.
    THIS IS A SENSITIVE ACTION and should have pre-checks.
    """
    print(f"TOOL: Executing trade for {user_id} with details: {trade_details}")
    time.sleep(1)
    return {
        "status": "success",
        "confirmation_id": f"trade_{random.randint(1000, 9999)}",
    }
