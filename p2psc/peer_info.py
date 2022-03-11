import requests
from appPublic.jsonConfig import getConfig
import json

P2PSC_CENTER_PID = 'p2psc_center'
class PeerInfos(object):
	def __init__(self):
		self.peers = {}
		self.rsa = RSA()
		config = getConfig()
		if config.known_peers_file:
		self._load_peer_info_from_file(config.known_peers_file)

	def _save_peer_info_to_file(self, fn):
		with codecs.open(fn, 'w', 'utf-8') as f:
			f.write(json.dumps(self.peers))

	def _load_peer_info_from_file(self, fn):
		with codecs.open(fn, 'r', 'utf-8') as f:
			b = f.read()
			self.peers = json.loads(b)

	def get_peer_info(self, pid, force_refind=False):
		if not force_refind:
			info = self.peers.get(pid)
			if info:
				info['last_time'] = time.time()
				return info
		return self.find_peer_info(pid)

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
		dd = d['pubkey'] + d['host'] + str(d[port'])
		if self.rsa.verify_sign(dd, s['sig']):
			d['last_time'] = time.time()
			self.peers[pid] = d
			return d
			
		return None
