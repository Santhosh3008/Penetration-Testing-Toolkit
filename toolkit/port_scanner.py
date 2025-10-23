# toolkit/port_scanner.py
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from tqdm import tqdm

def _check_port(target: str, port: int, timeout: float) -> int | None:
    try:
        with socket.create_connection((target, port), timeout=timeout):
            return port
    except Exception:
        return None

def scan_ports(target: str, start_port: int, end_port: int,
               timeout: float = 0.15, workers: int = 200, show_progress: bool = True) -> List[int]:
    """
    Concurrently scan ports in [start_port, end_port] and return a sorted list of open ports.
    """
    ports = range(start_port, end_port + 1)
    open_ports: List[int] = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_check_port, target, p, timeout): p for p in ports}

        if show_progress:
            for f in tqdm(as_completed(futures), total=len(futures), desc="Scanning ports"):
                try:
                    res = f.result()
                except Exception:
                    res = None
                if res:
                    open_ports.append(res)
        else:
            for f in as_completed(futures):
                try:
                    res = f.result()
                    if res:
                        open_ports.append(res)
                except Exception:
                    pass

    open_ports.sort()
    return open_ports
