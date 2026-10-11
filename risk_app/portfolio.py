"""Reproducible synthetic multi-asset portfolio and stress calculation utilities."""
import pandas as pd

def default_portfolio() -> pd.DataFrame:
    rows = [
        ("EQ001","Northstar Technology","Equity",150,180.0,"Technology",0.90),
        ("EQ002","Meridian Bank","Equity",900,42.0,"Financials",1.20),
        ("EQ003","Aster Consumer","Equity",500,76.0,"Consumer",0.75),
        ("EQ004","Helio Energy","Equity",700,31.0,"Energy",1.10),
        ("BD001","Sovereign 10Y Bond","Bond",1200,98.0,"Government",0.25),
        ("BD002","Investment Grade Credit","Bond",850,101.0,"Corporate",0.55),
        ("LN001","Commercial Real Estate Loan","Loan",1000,0.96,"Real Estate",0.80),
        ("LN002","SME Credit Facility","Loan",650,0.94,"SME",1.00),
        ("DV001","Equity Index Future","Derivative",20,320.0,"Equity Index",1.50),
        ("DV002","Rate Swap MTM","Derivative",1,18000.0,"Rates",0.70),
        ("DV003","FX Forward MTM","Derivative",1,9500.0,"FX",0.90),
        ("BD003","High Yield Bond","Bond",400,88.0,"High Yield",0.85),
    ]
    df = pd.DataFrame(rows, columns=["asset_id","asset_name","asset_class","quantity","unit_price","sector","risk_beta"])
    df["market_value"] = df["quantity"] * df["unit_price"]
    return df

SCENARIOS = {
    "Geopolitical escalation": {"Equity": -0.18, "Bond": -0.04, "Loan": -0.10, "Derivative": -0.22},
    "Inflation / rate shock": {"Equity": -0.12, "Bond": -0.14, "Loan": -0.06, "Derivative": -0.18},
    "Credit crisis": {"Equity": -0.25, "Bond": -0.16, "Loan": -0.28, "Derivative": -0.20},
    "Growth rebound": {"Equity": 0.12, "Bond": -0.03, "Loan": 0.05, "Derivative": 0.15},
    "Market liquidity shock": {"Equity": -0.20, "Bond": -0.09, "Loan": -0.18, "Derivative": -0.30},
}

def stress_portfolio(portfolio: pd.DataFrame, scenario: str, severity: float = 1.0,
                     custom_shocks: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Apply proportional asset-class shocks. severity scales all shocks; 1.0 = base case."""
    if not 0 <= severity <= 3:
        raise ValueError("severity must be between 0 and 3")
    if custom_shocks is not None:
        shocks = custom_shocks
    elif scenario in SCENARIOS:
        shocks = SCENARIOS[scenario]
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    out = portfolio.copy()
    if "market_value" not in out:
        out["market_value"] = out["quantity"] * out["unit_price"]
    out["shock_pct"] = out["asset_class"].map(shocks).fillna(0.0) * severity
    out["before_value"] = out["market_value"].astype(float)
    out["after_value"] = out["before_value"] * (1 + out["shock_pct"])
    out["pnl"] = out["after_value"] - out["before_value"]
    out["loss"] = -out["pnl"]
    before = float(out["before_value"].sum())
    after = float(out["after_value"].sum())
    pnl = after - before
    summary = {
        "scenario": scenario, "severity": float(severity), "before_value": before,
        "after_value": after, "pnl": pnl, "absolute_loss": max(0.0, -pnl),
        "loss_pct": (max(0.0, -pnl) / before * 100) if before else 0.0,
        "return_pct": (pnl / before * 100) if before else 0.0,
    }
    return out, summary

def class_contributions(stressed: pd.DataFrame) -> pd.DataFrame:
    result = stressed.groupby("asset_class", as_index=False).agg(
        before_value=("before_value", "sum"), after_value=("after_value", "sum"), pnl=("pnl", "sum"))
    result["loss"] = -result["pnl"]
    result["loss_contribution_pct"] = result["loss"] / result["loss"].sum() * 100 if result["loss"].sum() else 0.0
    return result.sort_values("loss", ascending=False)
