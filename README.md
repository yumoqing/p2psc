# p2psc
p2psc means peer to peer security communication for tcp and udp protocol. 
it use both one's private key and both sides's public key to encrypt, 
decrypt, transfer and verify a symmetiric key, and communicte with tis 
symmetric key to encode and decode communication data.

## Dependents
* asyncio
* cryptography
* uvloop


## TCP API
```
class TcpP2psc:
	def __init__(self, localhost, port, mypid, 
							myprivate_key, find_peer_info):
		pass

	def connect_peer(self, pid):
		pass

	def sendto_peer(self, pid, data)
		pass

	def run(self):
		pass

	def close_peer(self):
		pass

	def on_recvfrom_peer(self, pid, data)
		"""
		it need to return a bytes will be send back to client
		"""
		pass

	def on_ready(self):
		"""
		when the server ready
		"""
		pass

```
## Usage
class MyTcpP2psc(TcpP2psc):
	def on_recvfrom_peer(self, pid, data):
		...

	def on_ready(self):
		...

def find_peer_info(pid):
	...

p2psc = MyTcpP2psc(localhsot, 30000, 'test_server', 'my.pem', find_pper_info)
p2psc.run()


