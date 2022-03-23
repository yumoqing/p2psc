# p2psc
p2psc means peer to peer security communication for tcp and udp protocol. 
it use both one's private key and both sides's public key to encrypt, 
decrypt, transfer and verify a symmetiric key, and communicte with tis 
symmetric key to encode and decode communication data.

## Dependents
* asyncio
* cryptography
* uvloop
* appPublic

## Principle

We use RSA's encrypt/decrypt and sign/verify to make a safe hand shake
and use rc4 with a secret book switched in hand shake phase to 
encrypt/decrype data to deliver between the peer to peer hand shaked

## TCP API

### class P2PHandler

P2pHandler mantain self rsa key and peer's public key, and do the encrypt/decrypt work

### class TcpP2P
TcpP2P is a udp protocol for p2p
### class UdpP2P
UdpP2p is a udp protocol for p2p

## Usage

### TCP 
server side
```
import os, sys
import asyncio
from p2psc.p2phandler import P2PHandler
from p2psc.p2p import TcpP2P
from appPublic.jsonConfig import getConfig

class Server(TcpP2P):
    def on_recv(self, data):
        self.send(b'recv:' + data)

if __name__ == '__main__':
    pwd = os.getcwd()
    config = getConfig(pwd)
    loop = asyncio.get_event_loop()
    p2p = P2PHandler(loop=loop)
loop.run_until_complete( \
	p2p.run_as_server(ProtocolClass=Server))
    loop.run_forever()
```

client side
```
import os, sys
import asyncio
from p2psc.p2p import TcpP2P
from p2psc.p2phandler import P2PHandler
from appPublic.jsonConfig import getConfig

class Client(TcpP2P):
    def on_handshaked(self):
        self.send(b'this is a test text')

    def on_recv(self, data):
        d = data.decode('utf-8')
        print('data receive=', d)
        self.transport.close()
        loop = asyncio.get_running_loop()
        loop.stop()

if __name__ == '__main__':
    pwd = os.getcwd()
    config = getConfig(pwd)
    if len(sys.argv) < 2:
        print('Usage:\n%s peerid', sys.argv[1])
        sys.exit(1)

    loop = asyncio.get_event_loop()
    p2p = P2PHandler(loop=loop)
    c = loop.run_until_complete( p2p.connect_peer(sys.argv[1], ProtocolClass=Client))
    loop.run_forever()
```


