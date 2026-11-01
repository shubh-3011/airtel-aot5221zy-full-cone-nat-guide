"""Compare STUN public IPv4 mappings using one UDP socket; Python 3 only."""

import secrets
import socket
import struct

COOKIE = 0x2112A442
SERVERS = (("stun.cloudflare.com", 3478), ("stun.l.google.com", 19302),
           ("stun1.l.google.com", 19302))


def binding(sock, host, port):
    transaction = secrets.token_bytes(12)
    address = socket.gethostbyname(host)
    request = struct.pack("!HHI", 1, 0, COOKIE) + transaction
    sock.sendto(request, (address, port))
    packet, _ = sock.recvfrom(4096)
    if len(packet) < 20 or packet[8:20] != transaction:
        raise ValueError("Unexpected STUN response")
    message_type, length, cookie = struct.unpack("!HHI", packet[:8])
    if message_type != 0x0101 or cookie != COOKIE or len(packet) < 20 + length:
        raise ValueError("Invalid STUN binding response")
    offset = 20
    while offset + 4 <= 20 + length:
        attr_type, size = struct.unpack("!HH", packet[offset:offset + 4])
        value = packet[offset + 4:offset + 4 + size]
        offset += 4 + ((size + 3) // 4) * 4
        if attr_type not in (0x0020, 0x0001) or len(value) < 8 or value[1] != 1:
            continue
        mapped_port = struct.unpack("!H", value[2:4])[0]
        mapped_ip = value[4:8]
        if attr_type == 0x0020:
            mapped_port ^= COOKIE >> 16
            mapped_ip = bytes(a ^ b for a, b in zip(mapped_ip, struct.pack("!I", COOKIE)))
        return socket.inet_ntoa(mapped_ip), mapped_port
    raise ValueError("Response has no IPv4 mapped address")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("0.0.0.0", 0))
        sock.settimeout(5)
        for host, port in SERVERS:
            try:
                ip, mapped_port = binding(sock, host, port)
                print(f"{host}: {ip}:{mapped_port}")
            except (OSError, ValueError) as exc:
                print(f"{host}: {exc}")


if __name__ == "__main__":
    main()
