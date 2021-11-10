#!/usr/bin/env python3
import logging
import os
import signal
from pathlib import Path
from time import sleep

from dnslib import DNSLabel, QTYPE, RR, dns
from dnslib.proxy import ProxyResolver
from dnslib.server import DNSServer

# Inicializa el logger
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Convierte strings a tipos de dnslib
DNS_TYPES = {
    'A': (dns.A, QTYPE.A),
    'AAAA': (dns.AAAA, QTYPE.AAAA),
    'MX': (dns.MX, QTYPE.MX),
    'TXT': (dns.TXT, QTYPE.TXT)
}

# Clase que contiene un record de DNS, compatible con dnslib


class Record:
    def __init__(self, rname, rtype, args):
        self._rname = DNSLabel(rname)

        rd_cls, self._rtype = DNS_TYPES[rtype]

        self.rr = RR(
            rname=self._rname,
            rtype=self._rtype,
            rdata=rd_cls(*args),
            ttl=5,
        )

    def match(self, q):
        return q.qname == self._rname and (q.qtype == QTYPE.ANY or q.qtype == self._rtype)

    def __str__(self):
        return str(self.rr)


# Records de DNS
RECORDS = [
    Record('example.com', 'A', ('1.2.3.4',)),
    Record('test.com', 'A', ('4.3.3.4',)),
    Record('test.com', 'MX', ('Hola Mundo Test',)),

    Record('redesce.com', 'TXT', ('Hola Mundo Redes',)),
    Record('redesce.com', 'A', ('99.88.77.66',)),
    Record('redesce.com', 'AAAA', ('2001:0db8:85a3:0000:0000:8a2e:0370:7334',)),

    Record('tecdigital.tec.ac.cr', 'TXT', ('Record del TD hack',)),
    Record('tecdigital.tec.ac.cr', 'A', ('35.232.39.227',)),
    Record('tecdigital.tec.ac.cr', 'AAAA', ('2001:0db8:85a3:0000:0000:0000:0000:0000',)),
]

# Clase que resuelve consultas de DNS, compatible con dnslib


class Resolver(ProxyResolver):
    def __init__(self, upstream):
        super().__init__(upstream, 53, 5)
        self.records = RECORDS

    def resolve(self, request, handler):
        type_name = QTYPE[request.q.qtype]
        reply = request.reply()
        for record in self.records:
            if record.match(request.q):
                reply.add_answer(record.rr)

        if reply.rr:
            logger.info(
                'encontrado record para %s[%s], %d entradas', request.q.qname, type_name, len(reply.rr))
            return reply

        logger.info(
            'no se encontró localmente, buscando en DNS público %s[%s]', request.q.qname, type_name)
        return super().resolve(request, handler)


# Maneja el SIGINT para terminar el programa
def handle_sig(signum, frame):
    logger.info('pid=%d, obtuvo señal %s, saliendo...',
                os.getpid(), signal.Signals(signum).name)
    exit(0)


# Main
if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handle_sig)

    # Configuraciónd de dnslib
    port = int(os.getenv('PORT', 53))
    # Se utilizará este servidor como DNS público
    upstream = os.getenv('UPSTREAM', '8.8.8.8')
    resolver = Resolver(upstream)
    udp_server = DNSServer(resolver, port=port)
    tcp_server = DNSServer(resolver, port=port, tcp=True)

    logger.info(
        'iniciando servidor DNS en el puerto %d, con servidor upstream "%s"', port, upstream)
    udp_server.start_thread()
    tcp_server.start_thread()

    try:
        while udp_server.isAlive():
            sleep(1)
    except KeyboardInterrupt:
        pass
