#!/usr/bin/python3

import datetime
import signal
import socket
import subprocess
import sys
import time
from multiprocessing import Process


def isLoopback(ip: str) -> bool:
    return ip in ["127.0.0.1", "::1"]


def isIpv4MappedIpv6(ip: str) -> bool:
    try:
        rawIp = socket.inet_pton(socket.AF_INET6, ip)
        return rawIp.startswith(b'\x00' * 10 + b'\xff' * 2)
    except socket.error:
        return False


def extractIpv4FromIpv6(ip: str) -> str:
    if not isIpv4MappedIpv6(ip):
        raise ValueError(f"{ip} is not an IPv4-mapped IPv6 address")

    rawIpv6 = socket.inet_pton(socket.AF_INET6, ip)
    rawIpv4 = rawIpv6[-4:]
    return socket.inet_ntop(socket.AF_INET, rawIpv4)


def writeLog(family: str, ip: str, port: int) -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{family}] Caught {ip} on port {port}"
    print(log_entry, flush=True)
    try:
        with open("/var/log/iptrap.log", "a") as f:
            f.write(log_entry)
            f.write('\n')
    except BaseException as e:
        print(f"[!] Failed to write log to file: {e}", file=sys.stderr)


def banIp_firewalld(ip: str, family: str) -> None:
    print(f"Adding firewalld rule for {ip}", flush=True)
    try:
        subprocess.run(["firewall-cmd", "--add-rich-rule", f"rule family=\"{family}\" source address=\"{ip}\" drop"])
    except BaseException as e:
        print(f"[!] Failed to run command: {e}", file=sys.stderr)


def apply_firewalld() -> None:
    print(f"Saving firewalld rules", flush=True)
    try:
        subprocess.run(["firewall-cmd", "--runtime-to-permanent"])
    except BaseException as e:
        print(f"[!] Failed to run command: {e}", file=sys.stderr)


class Trap(Process):
    def __init__(self, port: int):
        super().__init__(name=f"IPTrap on :{port}", daemon=True)
        self.s: socket.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.port: int = port

    def stop(self) -> None:
        print(f"Stopping {self.name}", flush=True)
        try:
            self.s.shutdown(socket.SHUT_RDWR)
            self.s.close()
            self.terminate()
        except BaseException as e:
            if type(e) is not KeyboardInterrupt:
                print(f"[!] Error stopping trap on port {self.port}: {e}", file=sys.stderr)

    def run(self) -> None:
        print(f"Initializing trap on port {self.port}", flush=True)
        self.s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.s.bind(("::", self.port))
            self.s.listen(5)
            while True:
                c, addr = self.s.accept()
                c.send(bytearray("BUSTED\n", encoding="ASCII"))
                c.close()
                ip = extractIpv4FromIpv6(addr[0]) if isIpv4MappedIpv6(addr[0]) else addr[0]
                if isLoopback(ip):
                    continue
                family = "ipv4" if ":" not in ip else "ipv6"
                writeLog(family, ip, self.port)
                banIp_firewalld(ip, family)
        except BaseException as e:
            if type(e) is not KeyboardInterrupt:
                print(f"[!] Error running trap on port {self.port}: {e}", file=sys.stderr)


def main():
    ports = []
    traps = []

    for a in sys.argv[1:]:
        try:
            port: int = int(a)
            if port <= 0:
                raise ValueError
            ports.append(port)
        except BaseException as e:
            print(f"[!] Skipping invalid argument \"{a}\": {e}", file=sys.stderr)

    if len(ports) == 0:
        print("[!] No valid ports found, exiting", file=sys.stderr)
        exit(1)

    def shutdownHook(_, __):
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdownHook)

    print("IPTrap is starting", flush=True)
    for port in ports:
        trap: Trap = Trap(port)
        traps.append(trap)
        trap.start()

    try:
        while True:
            time.sleep(1000)
    except BaseException:
        print("IPTrap is being stopped", flush=True)
        for trap in traps:
            trap.stop()
        apply_firewalld()


if __name__ == "__main__":
    main()
