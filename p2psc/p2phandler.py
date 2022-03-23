
import os
import time
import codecs
import functools
import requests
from appPublic.jsonConfig import getConfig
from appPublic.rsa import RSA
import json
import random
import socket
P2PSC_CENTER_PID = 'p2psc_center'
from .p2p import TcpP2P
import concurrent.futures

class P2PHandler(object):
	def __init__(self, loop=None):
		if loop is None:
			loop = asyncio.get_event_loop()
		self.loop = loop
		self.peers = {}
		self.rsa = RSA()
		config = getConfig()
		self._load_my_info()
		self._load_secret_original()
		self.conns = {}
		self.excutor = concurrent.futures.ThreadPoolExecutor(
			max_workers=300
		)
		if config.known_peers_file:
			self._load_peers_info_from_file(config.known_peers_file)

	def set_peer_conn(self, peer_id, protocol):
		self.conns[peer_id] = protocol

	def get_peer_conn(self, peer_id):
		return self.conns.get(peer_id)

	def bridge(self, peer1_id, peer2_id):
		p1 = self.get_peer_conn(peer1_id)
		p2 = self.get_peer_conn(peer2_id)
		def data_received1(data):
			p2.transport.write(data)
		def data_received2(data):
			p1.transport.write(data)
		p1.data_received = data_received1
		p2.data_received = data_received2

	def _load_secret_original(self):
		config = getConfig()
		with open(config.secret_original_file, 'rb') as f:
			self.secret_original = f.read()
	
	def new_secret_book(self):	
		f = random.random() * 0.88
		solen = len(self.secret_original) 
		p = int(f * solen)
		lenth=100 # int(0.1 * solen)
		return self.secret_original[p:p+lenth]

	def verify_peer_pubkey(self, peerid, pubkey):
		txt = pubkey.decode('utf-8')
		pk = self.get_peer_pubkey(peerid)
		if pk is None:
			return False

		if txt == self.rsa.publickeyText(pk):
			return True
		return None
		
	def sign(self, buffer):
		return self.rsa.sign_bdata(self.my_prikey, buffer)

	def check_peer_sign(self, pid, buffer, sign):
		pk = self.get_peer_pubkey(pid)
		return self.rsa.check_sign_bdata(pk, buffer, sign)

	def peer_encode(self, pid, buffer):
		pk = self.get_peer_pubkey(pid)
		return self.rsa.encode_bytes(pk, buffer)

	def me_decode(self, buffer):
		return self.rsa.decode_bytes(self.my_prikey, buffer)

	def get_myid(self):
		return self.config['peer_id']

	def get_mypubkey(self):
		return self.rsa.publickeyText(self.config['pubkey']).encode('utf-8')

	def _load_my_info(self):
		config = getConfig()
		with codecs.open(config.xconfig, 'r', 'utf-8') as f:
			self.config = json.loads(f.read())

		self.my_prikey = self.rsa.read_privatekey(config.my_prikey_file)
		self.config['pubkey'] = self.rsa.create_publickey(self.my_prikey)

	def _save_peers_info_to_file(self, fn):
		with codecs.open(fn, 'w', 'utf-8') as f:
			f.write(json.dumps(self.peers))

		for pid, info in self.peers.items():
			pk = self.rsa.publickeyText(info['pubkey'])
			self._save_peer_pubkey(pid, pk)

	def _load_peers_info_from_file(self, fn):
		with codecs.open(fn, 'r', 'utf-8') as f:
			b = f.read()
			self.peers = json.loads(b)

		for pid, info in self.peers.items():
			pk = self._load_peer_pubkey(pid)
			info['pubkey'] = self.rsa.publickeyFromText(pk)
			

	def get_myaddress(self):
		host = socket.gethostbyname(self.config['host'])
		port = self.config['port']
		return host, port

	def get_peer_address(self, pid):
		p = self.get_peer_info(pid)
		if p is None:
			return None, None
		h = socket.gethostbyname(p['host'])
		p = p['port']
		return h, p

	def get_peer_pubkey(self, pid):
		info = self.get_peer_info(pid)
		if info is not None:
			return info['pubkey']
		return None

	def get_peer_info(self, pid, force_refind=False):
		if not force_refind:
			info = self.peers.get(pid)
			if info:
				info['last_time'] = time.time()
				return info
		return self.find_peer_info(pid)

	def _load_peer_pubkey(self, pid):
		config = getConfig()
		fn = os.path.join(config.peer_pubkey_path, f'{pid}.pubkey.pem')
		with codecs.open(fn, 'r', 'utf-8') as f:
			return f.read()
		
	def _save_peer_pubkey(self, pid, pubkey):
		config = getConfig()
		fn = os.path.join(config.pubkey_path, f'{pid}.pubkey.pem' )
		with codecs.open(fn, 'w', 'utf-8') as f:
			f.write(pubkey)

	def find_peer_info(self, pid):
		"""
		from center to get a peer's information
		{
			"pubkey":".....",
			"host":"....",
			"port":xxxxx,
			"sig":"....."
		}
		where sig is center sig the string: pubkey+host+str(port)
		this function need to know the center's pubkey
		"""

		config = getConfig()
		peer_info_url = config.find_peer_info_url
		params = {
			'id': pid
		}
		x = requests.get(peer_info_url, params=params)
		d = json.loads(x.text)
		pk = self.get_peer_info(P2PSC_CENTER_PID)['pubkey']
		dd = d['pubkey'] + d['host'] + str(d['port'])
		if self.rsa.check_sign_bdata(pk, dd.encode('utf-8'), s['sig']):
			self._save_peer_pubkey(pid, d['pubkey'])
			d['pubkey'] = self.rsa.publickeyFromText(d['pubkey'])
			d['last_time'] = time.time()
			self.peers[pid] = d
			return d
			
		return None

	def create_protocol(self, ProtocolClass, peer_id=None):
		return ProtocolClass(self, self.get_myid(), peer_id=peer_id)

	
	async def connect_peer(self, peer_id, ProtocolClass=TcpP2P):
		f = functools.partial(self.create_protocol, ProtocolClass, peer_id)
		pinfo = self.get_peer_info(peer_id)
		h = socket.gethostbyname(pinfo['host'])
		p = pinfo['port']
		client = await self.loop.create_connection(f, h, p)

	async def run_as_server(self, ProtocolClass=TcpP2P):
		f = functools.partial(self.create_protocol, ProtocolClass)
		h,p = self.get_myaddress()
		self.server = await self.loop.create_server(f, 
									h, p)

	def create_secret_book(self):
		alpha=' qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890!@#$%^&*(),./<>?'
		la = len(alpha)
		x = ""
		for i in range(113):
			j = int(random.random() * la)
			x = f'{x}{alpha[j]}'
		return x.encode('utf-8')
