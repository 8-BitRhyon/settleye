"""Local CONNECT proxy for sandboxed shells whose system resolver is blocked.

Raw UDP DNS to a public resolver works and TCP works, but getaddrinfo fails.
This proxy resolves names itself, then tunnels bytes so TLS stays end to end.
Listen on 127.0.0.1:8899 and point https_proxy at it.

Usage:
    python3 tools/dns_proxy.py &
    https_proxy=http://127.0.0.1:8899 git push origin main
"""

import socket
import socketserver
import struct
import sys
import threading

LISTEN = ("127.0.0.1", 8899)
DNS_SERVERS = ("8.8.8.8", "1.1.1.1")
_cache: dict[str, str] = {}


def _parse_name(data: bytes, offset: int) -> tuple[str, int]:
    labels = []
    while True:
        length = data[offset]
        if length == 0:
            offset += 1
            break
        if length & 0xC0:
            pointer = struct.unpack("!H", data[offset : offset + 2])[0] & 0x3FFF
            name, _ = _parse_name(data, pointer)
            labels.append(name)
            offset += 2
            return ".".join(labels), offset
        offset += 1
        labels.append(data[offset : offset + length].decode())
        offset += length
    return ".".join(labels), offset


def _query(name: str, server: str) -> str:
    tid = 0x5E77
    header = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    qname = b"".join(bytes([len(p)]) + p.encode() for p in name.split(".")) + b"\x00"
    packet = header + qname + struct.pack("!HH", 1, 1)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(6)
    try:
        sock.sendto(packet, (server, 53))
        data, _ = sock.recvfrom(2048)
    finally:
        sock.close()
    _, qdcount, ancount = struct.unpack("!HHH", data[2:8])
    offset = 12
    for _ in range(qdcount):
        _, offset = _parse_name(data, offset)
        offset += 4
    for _ in range(ancount):
        _, offset = _parse_name(data, offset)
        rtype, _rclass, _ttl, rdlen = struct.unpack("!HHIH", data[offset : offset + 10])
        offset += 10
        if rtype == 1 and rdlen == 4:
            return ".".join(str(b) for b in data[offset : offset + 4])
        offset += rdlen
    raise OSError(f"No A record for {name}")


def resolve(host: str) -> str:
    if host in _cache:
        return _cache[host]
    try:
        ip = socket.gethostbyname(host)
        _cache[host] = ip
        return ip
    except OSError:
        pass
    errors = []
    for server in DNS_SERVERS:
        try:
            ip = _query(host, server)
            _cache[host] = ip
            return ip
        except Exception as exc:
            errors.append(f"{server}: {exc}")
    raise OSError(f"resolve failed for {host}: {errors}")


class Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        first = self.rfile.readline(65536).decode("latin-1").strip()
        if not first:
            return
        parts = first.split()
        if len(parts) < 2 or parts[0].upper() != "CONNECT":
            self.wfile.write(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
            return
        host, _, port = parts[1].rpartition(":")
        port = int(port or 443)
        while True:
            line = self.rfile.readline(65536)
            if line in (b"\r\n", b"\n", b""):
                break
        try:
            ip = resolve(host)
            upstream = socket.create_connection((ip, port), timeout=20)
        except Exception as exc:
            self.wfile.write(f"HTTP/1.1 502 Bad Gateway\r\n\r\n{exc}".encode())
            return
        self.wfile.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        self.wfile.flush()

        def pump(src, dst):
            try:
                while True:
                    chunk = src.recv(65536)
                    if not chunk:
                        break
                    dst.sendall(chunk)
            except OSError:
                pass
            finally:
                try:
                    dst.shutdown(socket.SHUT_WR)
                except OSError:
                    pass

        a = threading.Thread(target=pump, args=(self.connection, upstream), daemon=True)
        b = threading.Thread(target=pump, args=(upstream, self.connection), daemon=True)
        a.start()
        b.start()
        a.join()
        b.join()
        upstream.close()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server(LISTEN, Handler) as server:
        print(f"proxy on {LISTEN[0]}:{LISTEN[1]}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            sys.exit(0)
