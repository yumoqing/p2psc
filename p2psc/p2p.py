"""
A protocol for peer to peer communication base on tcp protocol, only 
use both side's rsa private and public key to exchanges symmetric crypt key
and using the symmetric crypt key to encode and decode the data. 
"""
import asyncio
import time
import struct
from appPublic.app_logger import create_logger
from appPublic.uniqueID import getID
from appPublic.rc4 import KeyChain
from appPublic.app_logger import AppLogger
from .crc import gen_crc, check_crc
from .p2pexcept import *

HANDSHAKE_REQ=b'\x01'
HANDSHAKE_RESP=b'\x02'
RESHAKE_NEED=b'\x03'
ERROR_DATA=b'\x04'
NORMAL_DATA=b' '
NORMAL_REQ=b'\x30'
NORMAL_RESP=b'\x31'
STREAM_GONO=b'\x21'
STREAM_END=b'\x22'

BRIDGE_TO_REQ=b'\x03'
BRIDGE_TO_RESP=b'\x04'
BRIDGE_FOR_REQ=b'\x05'
BRIDGE_FOR_RESP=b'\x06'

class P2P(AppLogger):
	def __init__(self, handler, myid, peer_id=None):
		AppLogger.__init__(self)
		self.is_server = True if peer_id is None else False
		self.handler = handler
		self.status = 'init'
		self.myid = myid
		self.peer_id = peer_id
		if peer_id:
			self.handler.set_peer_conn(peer_id, self)
		self.myid_b = myid.encode('utf-8')
		self.send_buffer = ''
		if not self.is_server:
			self.secret_book = self.handler.create_secret_book()
			self.keychain = KeyChain(self.secret_book)
			self.session_id = None
		else:
			self.secret_book = None
			self.session_id = getID().encode('utf-8')

	def bridge_request(self, peer_id):
		self.target_pid = peer_id
		pk = self.handler.get_peer_pubkey(peer_id)

	
	def accept_bridge_request(self, peer_id):
		self.target_pid = peer_id
	
	def bridge_response(self, data):
		pass

	def accept_bridge_response(self, data):
		pass

	def bridge_transfer_request(self, request_id):
		pass

	def accept_bridge_transfer_request(self, request_id):
		pass

	def bridget_transfer_respnse(self,data):
		pass

	def accept_bridget_transfer_respnse(self,data):
		pass

	def pack_hand_shake(self, peer_id):
		timestamp = int(time.time())
		fmt = '!l%ds%ds' % (len(self.myid_b), len(self.secret_book))
		buffer = struct.pack(fmt, timestamp, self.myid_b, self.secret_book)
		sig_buffer = fmt.encode('utf-8') + b'||' + buffer
		crypt = self.handler.peer_encode(peer_id, sig_buffer)
		sign = self.handler.sign(crypt)
		fmt1 = '%ds%ds' % (len(crypt), len(sign))
		send_buffer = HANDSHAKE_REQ + fmt1.encode('utf-8') + \
						b'||' + struct.pack(fmt1, crypt, sign)
		return send_buffer

	def hand_shake(self, peer_id=None):
		if peer_id is None:
			peer_id = self.peer_id
		send_buffer = self.pack_hand_shake(peer_id)
		self.transport_write(send_buffer)

	def unpack_hand_shake_data(self, data):
		fmt, d = data.split(b'||', 1)
		fmt = fmt.decode('utf-8')
		crypt, sign = struct.unpack(fmt, d)
		bdata = self.handler.me_decode(crypt)
		fmt, stru = bdata.split(b'||', 1)
		fmt = fmt.decode('utf-8')
		timestamp, self.peer_id_b, self.secret_book = struct.unpack(fmt, stru)
		self.peer_id = self.peer_id_b.decode('utf-8')
		self.handler.set_peer_conn(self.peer_id, self)
		sign_check = self.handler.check_peer_sign(self.peer_id, crypt, sign)
		if not sign_check:
			self.transport.close()
			print('sign_check error')
			raise SignCheckError
		self.time_delta = int(time.time()) - timestamp
		self.keychain = KeyChain(self.secret_book, \
									time_delta=self.time_delta)

	def accept_hand_shake(self, data):
		self.unpack_hand_shake_data(data)
		crypt = self.handler.peer_encode(self.peer_id, self.session_id)
		sign = self.handler.sign(crypt)
		fmt = '!%ds%ds' % (len(crypt), len(sign))
		stru = struct.pack(fmt, crypt, sign)
		send_buffer = HANDSHAKE_RESP + fmt.encode('utf-8') + b'||' + stru
		self.transport_write(send_buffer)
		self.status = 'normal'
	
	def unpack_hand_shake_response_data(self, data):
		fmt, d = data.split(b'||', 1)
		fmt = fmt.decode('utf-8')
		crypt, sign = struct.unpack(fmt, d)
		sign_check = self.handler.check_peer_sign(self.peer_id, crypt, sign)
		if not sign_check:
			self.transport.close()
			raise SignCheckError
		self.session_id = self.handler.me_decode(crypt)
		
	def accept_hand_shake_response(self, data):
		self.unpack_hand_shake_response_data(data)
		self.status = 'normal'
		self.on_handshaked()

	def symmetric_encrypt_data(self, data):
		if self.status != 'normal':
			print('self.status=', self.status)
			raise ChannelNotReady()
		crypt = self.keychain.encode_bytes(data)
		return crypt

	def send(self, data):
		crc = gen_crc(data)
		bdata = crc+data
		crypt = self.symmetric_encrypt_data(bdata)
		self.transport_write(NORMAL_DATA + self.session_id + crypt)

	def transport_write(self, data):
		olen = len(data)
		self.transport.write(data)
		
	def accept_normal_data(self, data):
		if self.status != 'normal'
			return self.transport_write(self.reshake_package())

		bdata = self.keychain.decode_bytes(data)
		crc = bdata[:1]
		_bdata = bdata[1:]
		if check_crc(_bdata, crc):
			return self.on_recv(_bdata)
		else:
			self.transport.write(self.error_package())
			raise CRCError

	def reshake_package(self):
		return RESHAKE_NEED

	def error_package(self):
		return ERROR_DATA
		
	def data_handler(self, data):
		if data[0:1] == RESHAKE_NEED:
			self.status = 'init'
			self.hand_shake()
			return
		if data[0:1] == HANDSHAKE_REQ:
			if not self.is_server:
				print('not in server side, ignore it')
				return
			return self.accept_hand_shake(data[1:])
		if data[0:1] == HANDSHAKE_RESP:
			print('hand shake response data received')
			if self.is_server:
				print('in server side , ignore it')
				return
			return self.accept_hand_shake_response(data[1:])
		if data[0:1] == NORMAL_DATA:
			print('normal data received')
			dfrom = len(self.session_id) + 1
			session_id = data[1:dfrom]
			data = data[dfrom:]
			return self.accept_normal_data(data)
		print('Error data received', data)
		raise InvalidDateType()

	def on_recv(self, data):
		"""
		data already decoded
		"""

	def on_handshaked(self):
		"""
		connection already finish hand shake
		"""

class TcpP2P(asyncio.Protocol, P2P):
	def __init__(self, handler, myid, peer_id=None):
		asyncio.Protocol.__init__(self)
		P2P.__init__(self, handler, myid, peer_id=peer_id)

	def connection_made(self, transport):
		self.transport = transport
		if not self.is_server:
			self.hand_shake()

	def connection_lost(self, e):
		self.transport.close()
		if self.handler.get_peer_conn(self.peer_id):
			del self.handler.conns[self.peer_id]

	def data_received(self, data):
		return self.data_handler(data)

