# p2psc
p2psc use RSA's encrypt/decrypt and sign/verify to make a safe hand shake
and use rc4 with a secret book switched in hand shake phase to 
encrypt/decrype data to deliver between the peer to peer hand shaked

## Dependents
* asyncio
* cryptography
* uvloop
* appPublic

## Principle

* hand shake phase:
client use server's pubkey to encrypt client's peer_id and a secret book generated randomly, then use client's private key to sign. finally pack it as a hand shake request data, send to the server
when server received hand shake data, unpack the data to crypt data and a sign data, use server's private key to decrypt the crypt data, then unpack it to client's peer_id, and secret book, using the client peer_id find clien's public key, then use client public key to verify the sign.
if everything is OK, then generates a sessionid and encrypt it with client's public key, sign the crypt data with self private key, finally pack and send it bak to client
hand shake finish
* normal data communication
use secret book and current timestamp to generate a rc4 key, and encrypt/decrypt the data communicates between the two peers hand shaked.

## TCP API

### class P2PHandler

P2pHandler mantain self rsa key and peer's public key, and do the encrypt/decrypt work

### class TcpP2P
TcpP2P is a udp protocol for p2p
### class UdpP2P
UdpP2p is a udp protocol for p2p

## Usage

### TCP 
server.py under test folder
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

client.py under test folder
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
## Peer's configure file
P2psc need a conf/config.json file in somewhere to stores the p2p configure information.
it contains:
```
{
	"my_prikey_file":   "$[workdir]$/data/private_key.pem",
	"xconfig":          "$[workdir]$/data/config.json",
	"known_peers_file": "$[workdir]$/data/peers.json",
	"peer_pubkey_path": "$[workdir]$/data/pubkeys",
	"find_peer_info_url":"http://192.168.1.8:9999/api/get_peer_info.dspy"
}
```
In configure file, there are three variable can use, it meens:
* workdir
	current work folder where the programs run 
* ProgramPath
	the program folder
* home
	user home

### my_prikey_file
Self peer's private key file, in pem format, support to set access key

### xconfig
self peer node's configure information
```
{
	"peer_id":"test1.com",
	"host":"127.0.0.1",
	"port":10098
}
```
### known_peers_file
stores all known peer information
```
{
	"test2.com":{
		"peer_id":"test2.com",
		"host":"localhost",
		"port":10099
	}
}
```

### find_peer_info_url
A website store peer's public key and connect host and  port information

### peer_pubkey_path
The folder stores peer's public key, need write privilege
```
-rw-r--r--  1 ymq  staff  451 Mar 16 11:31 test2.com.pubkey.pem
```
### 
## Test
test source code in test folder, there are client.py and server.py in test folder
### start server
```
cd test1
python ../test/server.py
```

### start client
```
cd test2
python ../test/client.py test1.com
```
the result
```
