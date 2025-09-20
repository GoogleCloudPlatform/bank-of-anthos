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
