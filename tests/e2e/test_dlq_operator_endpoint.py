import io
import os


def test_execution_service_dlq_operator_endpoint():
    # Execution service should expose operator DLQ endpoint in code or docs
    path = os.path.join("execution_service.py")
    if not os.path.exists(path):
        pytest.skip("execution_service.py not present")
    content = open(path, "r").read()
    assert "/operator/dlq" in content or "operator/dlq" in content, "operator dlq endpoint not implemented in execution_service.py"
