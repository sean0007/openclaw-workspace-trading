import os
import sys

# Ensure the repository root is on sys.path so tests can import top-level modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Ensure sensible default env vars for local/CI test runs
os.environ.setdefault('SIGNER_API_KEY', 'local-test-signer')
os.environ.setdefault('EXECUTION_OPERATOR_API_KEY', 'test-operator-key')
os.environ.setdefault('OPENCLAW_ALLOW_LOCAL_SIGNER', 'false')
