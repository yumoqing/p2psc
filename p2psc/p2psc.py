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

class P2psc(AppLogger):
	def __init__(self, handler, myid, peer_id=None):
		AppLogger.__init__(self)
		self.is_server = True if peer_id is None else False
		self.handler = handler
		self.status = 'init'
		self.myid = myid
		self.peer_id = peer_id
		self.timestamp = time.time()
		if peer_id:
			self.handler.set_peer_conn(peer_id, self)
		self.myid_b = myid.encode('utf-8')

	def build_hand_shake_package(self):
		if self.status not in ['init', 'status_mismatch']:
			self.debug('status mismatch, can not hand shake')
			self.status = 'status_mismatch'
			raise StatusError
		self.secret_book = self.handler.create_secret_book()
		self.keychain = KeyChain(self.secret_book)
		self.session_id = None
		peer_id = self.peer_id
		self.status = 'handshaking'
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

	def unpack_hand_shake_data(self, data):
		self.secret_book = None
		self.session_id = getID().encode('utf-8')
		self.status = 'handshaking'
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
			self.debug('sign_check error')
			raise SignCheckError
		self.time_delta = int(time.time()) - timestamp
		self.keychain = KeyChain(self.secret_book, \
									time_delta=self.time_delta)

	def build_hand_shake_response_package(self):
		if self.status != 'handshaking':
			raise StatusError
		crypt = self.handler.peer_encode(self.peer_id, self.session_id)
		sign = self.handler.sign(crypt)
		fmt = '!%ds%ds' % (len(crypt), len(sign))
		stru = struct.pack(fmt, crypt, sign)
		send_buffer = HANDSHAKE_RESP + fmt.encode('utf-8') + b'||' + stru
		self.status = 'normal'
		return send_buffer

	def set_timestamp(self):
		self.timestamp = time.time()

	def unpack_hand_shake_response_package(self, data):
		if self.status != 'handshaking':
			self.status = 'status_mismatch'
			raise StatusError
		fmt, d = data.split(b'||', 1)
		fmt = fmt.decode('utf-8')
		crypt, sign = struct.unpack(fmt, d)
		sign_check = self.handler.check_peer_sign(self.peer_id, crypt, sign)
		if not sign_check:
			self.transport.close()
			raise SignCheckError
		self.session_id = self.handler.me_decode(crypt)
		self.status = 'normal'
		
	def build_normal_package(self, data):
		if self.status != 'normal':
			self.debug('self.status=%s', self.status)
			self.status = 'status_mismatch'
			raise ChannelNotReady()
		crc = gen_crc(data)
		bdata = crc+data
		crypt = NORMAL_DATA + self.keychain.encode_bytes(bdata)
		return crypt

	def unpack_normal_package(self, data):
		if self.status != 'normal':
			self.debug('self.status=%s', self.status)
			self.status = 'status_mismatch'
			raise ChannelNotReady()

		bdata = self.keychain.decode_bytes(data)
		crc = bdata[:1]
		_bdata = bdata[1:]
		if check_crc(_bdata, crc):
			return _bdata
		else:
			raise CRCError

	def reshake_package(self):
		return RESHAKE_NEED

	def error_package(self):
		return ERROR_DATA
		
