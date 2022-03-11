import socket
import asyncio
import uvloop
from appPublic.rsa import RSA
from appPublic.rc4 import KeyChain

class TcpP2psc:
	def __init__(self, localhost, port, mypid, 
							myprivate_key, find_peer_info):
		pass

	async def connect_peer(self, pid):
		pass

	async def sendto_peer(self, pid, data)
		pass

	async def run(self):
		pass

	def close_peer(self):
		pass

	async def on_recvfrom_peer(self, pid, data)
		"""
		it need to return a bytes will be send back to client
		"""
		pass

	async def on_ready(self):
		"""
		when the server ready
		"""
		pass

