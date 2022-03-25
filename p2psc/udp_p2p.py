"""
A protocol for peer to peer communication base on tcp protocol, only 
use both side's rsa private and public key to exchanges symmetric crypt key
and using the symmetric crypt key to encode and decode the data. 
"""
import asyncio
import time
import struct
from appPublic.app_logger import AppLogger
from appPublic.uniqueID import getID
from appPublic.rc4 import KeyChain
from .p2p import P2P
from .p2pexcept import *

class UP2P(P2P):
	def __init__(self, protocol, addr):
		P2P.__init__(self, protocol.handler, protocol.myid, 
							peer_id=protocol.peer_id)
		self.protocol = protocol
		self.remote_addr = addr
		self.timestamp_last()
	
	def transport_write(self, data, addr=None):
		if addr is None:
			addr = self.remote_addr
		self.transport.sendto(data, addr)
		self.debug('send data=%s',data)
		
	def on_recv(self, data):
		self.logger.debug('on_recv(%s) called', data)
		self.protocol.on_recv(data, self.remote_addr)

	def timestamp_last(self):
		self.timestamp = time.time()

	def on_handshaked(self):
		"""
		"""
		self.protocol.on_handshaked()
		
class UdpP2P(asyncio.DatagramProtocol, AppLogger):
	"""
	use myid + peer_id to identify a seesion
	so every data transfers need to twin id in the head
	
	"""
	def __init__(self, handler, myid, peer_id=None):
		super().__init__()
		self.handler = handler
		self.myid = myid
		self.peer_id = peer_id
		self.p2ps = {}
		self.remote_addr = None
		self.destroy_dummy = True
		if peer_id:
			self.remote_addr = self.handler.get_peer_address(peer_id)
			if not self.remote_addr:
				raise UnknownPeerError
		loop = asyncio.get_event_loop()
		loop.run_in_executor(self.handler.executor, self.destroy_dummy_p2p)
		self.debug('__init__() called')

	def create_p2p(self, addr):
		p2p = UP2P(self, addr)
		p2p.transport = self.transport
		self.update_p2p(p2p, addr)
		return p2p

	def p2pkey(self, addr):
		return addr[0] + '_' + str(addr[1])
	
	def update_p2p(self, p2p, addr):
		k = self.p2pkey(addr)
		self.p2ps.update({k:p2p})

	def get_p2p(self, addr):
		k = self.p2pkey(addr)
		p2p = self.p2ps.get(k)
		if p2p is None:
			self.error('p2p not found by addr(%s)', addr)
			return None
		p2p.timestamp_last()
		return p2p

	def destroy_dummy_p2p(self):
		timeout = 5 * 60 # 30 minutes
		while self.destroy_dummy:
			ts = time.time()
			dummy = [ (k,p2p) for k,p2p in self.p2ps.items() if ts - p2p.timestamp >= timeout ]
			for k,v in dummy:
				del self.p2ps[k]
				self.debug('p2p[%s] deleted', k)
			time.sleep(10)

	def connection_made(self, transport):
		self.debug('connection_made() called')
		self.transport = transport
		if self.peer_id:
			p2p = self.create_p2p(self.remote_addr)
			p2p.hand_shake()
			self.logger.debug('p2p.hand_shake() called, status=%s', p2p.status)

	def connection_lost(self, e):
		self.logger.debug('connection_lost(%s)', e)
		self.transport.close()

	def datagram_received(self, data, addr):
		self.logger.debug('datagram_received(%s, %s) called', data, addr)
		p2p = self.get_p2p(addr)
		if p2p is None:
			p2p = self.create_p2p(addr)
		p2p.data_handler(data)
		self.logger.debug('p2p.datahandler() fininshed')

	def error_received(self, e):
		self.debug('error_received(%s) called', e)

	def on_handshaked(self, addr):
		"""
		"""
		pass

	def on_recv(self, data, addr):
		"""
		will call this hook function when data recevied from peer
		"""
		pass

	def send(self, data, addr=None):
		"""
		send data to peerid
		"""
		self.debug('send(%s,%s) called', data,addr)
		if addr is None:
			addr = self.remote_addr
		if addr is None:
			self.error('need a remote addr')
			raise MissRemoteAddr

		self.debug('addr(%s), p2ps=%s', addr, self.p2ps)
		p2p = self.get_p2p(addr)
		p2p.send(data)

	def stop(self):
		self.destroy_dummy = False
		if self.transport:
			self.transport.close()
			self.transport = None

