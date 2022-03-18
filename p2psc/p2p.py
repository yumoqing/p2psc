"""
A protocol for peer to peer communication base on tcp protocol, only 
use both side's rsa private and public key to exchanges symmetric crypt key
and using the symmetric crypt key to encode and decode the data. 
"""
import asyncio
import time
import struct
from appPublic.uniqueID import getID

HANDSHAKE_REQ=b'\x01'
HANDSHAKE_RESP=b'\02'
NORMAL_DATA=b' '

class ChannelNotReady(Exception):
	pass
class InvalidDataType(Exception):
	pass
class SignCheckError(Exception):
	pass

class P2P(object):
	def __init__(self, handler, myid, peer_id=None):
		self.is_server = True if peer_id is None else False
		self.handler = handler
		self.status = 'init'
		self.myid = myid.enode('utf-8')
		self.peer_id = peer_id.encode('utf-8')
		self.send_buffer = ''
		if not self.is_server:
			self.secret_book = self.handler.create_secret_book()
			self.keychain = KeyChain(self.secret_book)
			self.session_id = None
		else:
			self.secret_book = None
			self.session_id = getID().encode('utf-8')

	def hand_shake(self):
		timestamp = int(time.time())
		fmt = '!l%ds%ds' % (len(self.myid), len(self.secret_book))
		buffer = struct.pack(fmt, timestamp, self.myid, self.secret_book)
		sig_buffer = fmt.encode('utf-8') + b'||' + buffer
		crypt = self.handler.peer_encode(self.peer_id, sig_buffer)
		sign = self.handler.sign(crypt)
		fmt1 = '%ds%ds' % (len(crypt), len(sign)
		send_buffer = HANDSHAKE_REQ + fmt1.encode('utf-8') + \
						b'||' + struct.pack(fmt1, crypt, sign)
		self.trasnport.write(send_buffer)

	def unpack_hand_shake_data(self, data):
		fmt, d = data.split(b'||')
		fmt = fmt.decode('utf-8')
		crypt, sign = struct.unpack(fmt, d)
		sign_check = self.handler.check_peer_sign(self.peer_id, crypt, sign)
		if not sign_check:
			self.transport.close()
			raise SignCheckError
		bdata = self.handler.me_decode(crypt)
		fmt, stru = bdata.split(b'||')
		fmt = fmt.decode('utf-8')
		timestamp, self.peer_id, self.secret_book = struct.unpack(fmt, stru)
		self.time_delta = int(time.time()) - timestamp
		self.keychain = KeyChain(self.secret_book, \
									time_delta=self.time_delta)

	def accept_hand_shake(self, data):
		self.unpack_hand_shake_data(data)
		crypt = self.handler.peer_encode(self.peer_id, self.seesion_id)
		sign = self.handler.sign(self.myid, crypt)
		fmt = '!%ds%ds' % (len(crypt), len(sign))
		stru = struct.pack(fmt, crypt, sign)
		send_buffer = HANDSHAKE_RESP + fmt.encode('utf-8') + b'||' + stru
		self.status = 'normal'
	
	def unpack_hand_shake_response_data(self, data):
		fmt, d = split(b'||')
		fmt = fmt.decode('utf-8')
		crypt, sign = struct.unpack(fmt, d)
		sign_check = self.handler.check_peer_sign(self.peer_id, crypt, sign)
		if not sign_check:
			self.transport.close()
			raise SignCheckError
		self.session_id = self.handler.me_decode(crypt)
		
	def accept_hand_shake_response(self, data):
		self.unpack_hand_shake_response_data(data)
		self.on_handshaked()
		self.status = 'normal'

	def send(self, data):
		if self.status != 'normal':
			raise ChannelNotReady()
		crypt = self.keychain.encode_bytes(data)
		self.transport.write(NORMAL_DATA + self.session_id + crypt)

	def accept_normal_data(self, data):
		bdata = self.keychain.decode_bytes(data)
		return self.on_recv(bdata)

	def data_received(self, data):
		if data[0:1] == HANDSHAKE_REQ:
			if not self.is_server
				return
			return self.accept_hand_shake(data[1:])
		if data[0:1] == HANDSHAKE_RESP:
			if self.is_server:
				return
			return self.accept_hand_shke_response(data[1:])
		if data[0:1] == NORMAL_DATA:
			dfrom = len(self.session_id) + 1
			session_id = data[1:dfrom]
			data = data[dfrom:]
			return self.accept_normal_data(data)
		raise InvalidDateType()

	def on_recv(self, data):
		"""
		data already decoded
		"""

	def on_handshaked(self):
		"""
		connection already finish hand shake
		"""

class TcpP2p(asyncio.Protocol, P2P):
	def __init__(self, handler, myid, peer_id=None):
		asyncio.Protocol.__init__()
		P2P.__init__(self, handler, myid, peer_id=peer_id)

	def connection_made(self, transport):
		self.transport = transport
		if not self.is_server:
			self.hand_shake()

	def connection_lost(self, e):
		self.transport.close()

