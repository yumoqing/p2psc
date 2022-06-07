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
from .p2psc import *
from .p2pexcept import *

class SecUdp(asyncio.DatagramProtocol, AppLogger):
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
		self.blocked_data = []
		self.idle_timeout = 3600
		self.destroy_dummy = True
		self.remote_addr = None
		self.set_idle_timeout()
		if peer_id:
			self.remote_addr = self.handler.get_peer_address(peer_id)
			if not self.remote_addr:
				raise UnknownPeerError
		else:
			loop = asyncio.get_event_loop()
			loop.run_in_executor(self.handler.executor, 
							self.destroy_dummy_p2p)

	def set_idle_timeout(self):
		pass

	def create_p2p(self, addr = None):
		p2p = P2psc(self.handler, self.myid, peer_id = self.peer_id)
		if addr is None:
			addr = self.remote_addr
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
		p2p.set_timestamp()
		return p2p

	def destroy_dummy_p2p(self):
		timeout = self.idle_timeout
		while self.destroy_dummy:
			ts = time.time()
			dummy = [ (k,p2p) for k,p2p in self.p2ps.items() if ts - p2p.timestamp >= timeout ]
			for k,v in dummy:
				del self.p2ps[k]
				self.info('p2p[%s] deleted', k)
			timestamps = [ ts - i.timestamp for i in self.p2ps.values() ]
			time.sleep(1)

	def connection_made(self, transport):
		# self.info('connection_made() called')
		self.transport = transport
		if self.peer_id:
			p2p = self.create_p2p()
			self.hand_shake()
			self.logger.info('p2p.hand_shake() called, status=%s', p2p.status)

	def connection_lost(self, e):
		self.logger.debug('connection_lost(%s)', e)
		self.transport.close()

	def datagram_received(self, data, addr):
		self.logger.info('datagram_received(%s, %s) called', data, addr)
		p2p = self.get_p2p(addr)
		if p2p is None:
			p2p = self.create_p2p(addr=addr)
		if data[0:1] == RESHAKE_NEED:
			p2p.status = 'init'
			self.hand_shake()
			return
		if data[0:1] == HANDSHAKE_REQ:
			return self.accept_hand_shake(data[1:], addr)
		if data[0:1] == HANDSHAKE_RESP:
			return self.accept_hand_shake_response(data[1:], addr)
		if data[0:1] == NORMAL_DATA:
			data = data[1:]
			return self.accept_normal_data(data, addr)
		self.info('Error data type(%s) received', data[0:1])
		raise InvalidDataType()

	def error_received(self, e):
		self.debug('error_received(%s) called', e)

	def on_handshaked(self):
		"""
		"""
		pass

	def on_recv(self, data, addr):
		"""
		will call this hook function when data recevied from peer
		"""
		pass

	def _udp_send(self, data, addr):
		# self.info('data send=%s, addr=%s', data, addr)
		self.transport.sendto(data, addr)
		
	def hand_shake(self):
		p2p = self.get_p2p(self.remote_addr)
		buf = p2p.build_hand_shake_package()
		self._udp_send(buf, self.remote_addr)

	def accept_hand_shake_response(self, data, addr):
		p2p = self.get_p2p(self.remote_addr)
		p2p.unpack_hand_shake_response_package(data)
		for d in self.blocked_data:
			self.send(d, self.remote_addr)
		self.blocked_data = []
		self.on_handshaked()

	def accept_hand_shake(self, data, addr):
		p2p = self.get_p2p(addr)
		p2p.unpack_hand_shake_data(data)
		buf = p2p.build_hand_shake_response_package()
		self._udp_send(buf, addr)
		for d in self.blocked_data:
			self.send(d, addr)
		self.blocked_data = []
		self.on_handshaked()
			
	def accept_normal_data(self, data, addr):
		p2p = self.get_p2p(addr)
		d = None
		try:
			d = p2p.unpack_normal_package(data)
		except ChannelNotReady as e:
			if self.remote_addr:
				self.hand_shake()
				return
			else:
				d = p2p.reshake_package()
				self._udp_send(d, addr)
				return
		self.on_recv(d, addr)

	def send(self, data, addr=None):
		"""
		send data to peerid
		"""
		# self.info('send(%s,%s) called', data,addr)
		if addr is None:
			addr = self.remote_addr
		if addr is None:
			self.error('need a remote addr')
			raise MissRemoteAddr

		p2p = self.get_p2p(addr)
		buf = None
		try:
			buf = p2p.build_normal_package(data)
		except ChannelNotReady as e:
			self.blocked_data.append(data)
			self.hand_shake()
			return
		except:
			return

		if buf is not None:
			self._udp_send(buf, addr)

	def stop(self):
		self.destroy_dummy = False
		if self.transport:
			self.transport.close()
			self.transport = None

