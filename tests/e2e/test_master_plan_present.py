import os


def test_master_plan_exists():
    # The master plan MUST be present at repo root for automated auditors
    assert os.path.exists("MASTER_TRADING_DESK_PLAN.md"), "MASTER_TRADING_DESK_PLAN.md missing"
