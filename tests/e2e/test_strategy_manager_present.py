import os


def test_strategy_manager_present():
    # Expect a process-managing strategy manager for isolation
    path = os.path.join("strategy_runtime", "strategy_manager.py")
    assert os.path.exists(path), f"Strategy manager missing: {path}"
