import os
import tempfile
from secrets_manager import get_secrets_manager, rotate_secret


def test_rotate_secret_with_stub(tmp_path):
    os.environ["SECRETS_BACKEND"] = "stub"
    path = str(tmp_path / "vaultstub.json")
    mgr = get_secrets_manager(path)
    # set an initial value via interface
    mgr.set_secret("exec_hmac_key", "initial")
    old = mgr.get_secret("exec_hmac_key").decode()
    new = rotate_secret("exec_hmac_key", manager=mgr)
    assert isinstance(new, str) and len(new) > 0
    updated = mgr.get_secret("exec_hmac_key").decode()
    assert updated != old
