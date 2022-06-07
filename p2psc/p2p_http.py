# from appPublic.http_client import Http_Client
import requests

class P2pHttpClient:
	def __init__(self, p2p):
		self.session = requests.Session()
		self.p2p = p2p



