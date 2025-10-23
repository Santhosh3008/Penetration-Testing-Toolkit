# main.py
import argparse
import os
import sys

from toolkit.port_scanner import scan_ports
from toolkit.brute_forcer import brute_force_login
from toolkit.vulnerability_scanner import test_sql_injection, test_xss
from toolkit.utils import is_valid_ip

# try colorama for green text (fallback to no color)
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    GREEN = Fore.GREEN
    RESET = Style.RESET_ALL
except Exception:
    GREEN = ""
    RESET = ""

def read_password_file(path):
    """Return list of cleaned password strings (strip BOMs/nulls/whitespace)."""
    if path == "-":
        data = sys.stdin.read()
        lines = [ln.strip() for ln in data.splitlines() if ln.strip()]
        return [clean_password(ln) for ln in lines]

    pw_path = os.path.abspath(path)
    if not os.path.exists(pw_path):
        print(f"[!] Password file not found: {pw_path}")
        return None

    # Try common encodings, but sanitize each line anyway.
    encodings = ["utf-8", "utf-8-sig", "utf-16", "latin-1"]
    last_exc = None
    for enc in encodings:
        try:
            with open(pw_path, "r", encoding=enc, errors="replace") as f:
                raw_lines = f.read().splitlines()
            cleaned = [clean_password(ln) for ln in raw_lines if ln.strip()]
            if cleaned:
                return cleaned
        except Exception as e:
            last_exc = e
            continue

    print(f"[!] Could not read password file. Last error: {last_exc}")
    return None

def clean_password(s: str) -> str:
    """
    Remove BOMs and embedded nulls and surrounding whitespace.
    Handles common BOM markers: UTF-8 BOM (U+FEFF), 'ï»¿' artifacts, and null bytes.
    """
    if s is None:
        return ""
    # Normalize to str, then drop nulls and BOM chars.
    s = str(s)
    # remove Unicode BOM
    s = s.lstrip("\ufeff")
    # remove common mis-decoded BOM sequences
    s = s.replace("ï»¿", "")
    # remove null bytes often from wrong decoding of UTF-16
    s = s.replace("\x00", "")
    return s.strip()

def main():
    parser = argparse.ArgumentParser(description="Penetration Testing Toolkit")
    try:
        subparsers = parser.add_subparsers(dest="command", required=True)
    except TypeError:
        subparsers = parser.add_subparsers(dest="command")

    # Port Scanner
    port_parser = subparsers.add_parser("scan", help="Scan open ports on a target")
    port_parser.add_argument("target", help="Target IP address")
    port_parser.add_argument("--start", type=int, default=1, help="Starting port")
    port_parser.add_argument("--end", type=int, default=1024, help="Ending port")

    # Brute Forcer
    brute_parser = subparsers.add_parser("brute", help="Perform a brute-force attack")
    brute_parser.add_argument("url", help="Login page URL")
    brute_parser.add_argument("username", help="Username to test")
    brute_parser.add_argument("password_file", help="File containing password list (use '-' for stdin)")

    # Vulnerability Scanner
    vuln_parser = subparsers.add_parser("vuln", help="Test for vulnerabilities")
    vuln_parser.add_argument("url", help="URL to test")
    vuln_parser.add_argument("param", help="Parameter to test")

    args = parser.parse_args()

    if args.command == "scan":
        if not is_valid_ip(args.target):
            print("[!] Invalid IP address")
            sys.exit(1)
        open_ports = scan_ports(args.target, args.start, args.end)
        print(f"Open ports: {open_ports}")

    elif args.command == "brute":
        passwords = read_password_file(args.password_file)
        if passwords is None:
            sys.exit(1)
        if not passwords:
            print("[!] Password file is empty.")
            sys.exit(1)

        result = brute_force_login(args.url, args.username, passwords)
        if result:
            user, pwd = result
            # print success on its own line in green
            print()  # end the inline "Trying..." line before printing success
            print(f"{GREEN}Login successful: ({user!r}, {pwd!r}){RESET}")
            sys.exit(0)
        else:
            print()  # end inline attempts
            print("Login failed")
            sys.exit(2)

    elif args.command == "vuln":
       # SQLi test
        print("Testing for SQL Injection...", end=" ")
        try:
            sqli = test_sql_injection(args.url, args.param)
        except Exception as e:
            print(f"[error: {e}]")
            sqli = False

        if sqli:
            print("SQL Injection vulnerability found!")
        else:
            print("No SQL Injection found.")

        print()  # blank line between checks

        # XSS test
        print("Testing for XSS...", end=" ")
        try:
            xss = test_xss(args.url, args.param)
        except Exception as e:
            print(f"[error: {e}]")
            xss = False

        if xss:
            print("XSS vulnerability found!")
        else:
            print("No XSS found.")



if __name__ == "__main__":
    main()
