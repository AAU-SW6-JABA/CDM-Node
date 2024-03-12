#!/usr/bin/env python3
from dotenv import load_dotenv
import os

from optparse import OptionParser
from scapy.all import sniff

import asyncio
import logging
import grpc

from common.imsi_sniffer import IMSISniffer
from route_guide_pb2_grpc import RoutesStub


async def main() -> None:
    parser = OptionParser(usage="%prog: [options]")
    parser.add_option("-i", "--iface", dest="iface", default="lo", help="Interface (default : lo)")
    parser.add_option("-p", "--port", dest="port", default="4729", type="int", help="Port (default : 4729)")
    parser.add_option("-s", "--sniff", action="store_true", dest="sniff",
                      help="sniff on interface instead of listening on port (require root/suid access)")
    (options, args) = parser.parse_args()

    address: str = os.getenv("GRPC_SERVER_ADDRESS")

    if not address:
        raise Exception("Failed to load address")

    async with grpc.aio.insecure_channel(address) as channel:
        stub = RoutesStub(channel)
        imsi_sniffer = IMSISniffer(stub)

        if options.sniff:
            sniff(iface=options.iface, filter=f"port {options.port} and not icmp and udp",
                  prn=imsi_sniffer.find_imsi_from_pkt,
                  store=0)
        else:
            imsi_sniffer.udpserver(port=options.port)


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    asyncio.get_event_loop().run_until_complete(main())