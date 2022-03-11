# p2psc
p2psc means peer to peer security communication for tcp and udp protocol. 
it use both one's private key and both sides's public key to encrypt, 
decrypt, transfer and verify a symmetiric key, and communicte with tis 
symmetric key to encode and decode communication data.

## Dependents


## TCP API
class P2pscTcpClient:
	def __init__(self, server, port, mypid, 
							myprivate_key, server_public_key):
		pass

	def send_bytes(self, data):
		pass

	def recv_bytes(self, size=4096):
		pass

	def close()
		pass

class P2pscTcpServer:
	def __init__(self, localhost, port, mypid, 
							myprivate_key, get_peer_pubkey):
		pass

	def on_recv_bytes(self, pid, data)
		"""
		it need to return a bytes will be send back to client
		"""

	def close()


## Usage

