import sys
import os
import codecs
import json
import random
from appPublic.jsonConfig import getConfig
from appPublic.folderUtils import ProgramPath, _mkdir
from appPublic.rsa import RSA
from appPublic.rc4 import KeyChain

def gen_keys(pid, passwd=None):
	config = getConfig()
	rsa = RSA()
	prikey = rsa.create_privatekey()
	fn = config.my_prikey_file
	rsa.write_privatekey(prikey, fn, password=passwd)
	pk = rsa.create_publickey(prikey)
	fn1 = os.path.join(os.path.dirname(fn), f'{pid}.pubkey.pem')
	rsa.write_publickey(pk, fn1)

def gen_xconfig(pid, host, port):
	d = {
		"peer_id":pid,
		"host":host,
		"port":port
	}
	config = getConfig()
	x = json.dumps(d, indent=4)
	with codecs.open(config.xconfig, 'w', 'utf-8') as f:
		f.write(x)

def gen_empty_peers():
	config = getConfig()
	with codecs.open(config.known_peers_file, "w", "utf-8") as f:
		f.write('''{
}''')
	
	_mkdir(config.peer_pubkey_path)

if __name__ == '__main__':
	workdir = os.getcwd()
	config = getConfig(workdir)
	passwd = None
	if len(sys.argv) < 4:
		print('Usage:\n%s myid host port' % sys.argv[0])
		sys.exit(1)
	pid = sys.argv[1]
	host = sys.argv[2]
	port = int(sys.argv[3])

	gen_keys(sys.argv[1], passwd=passwd)
	gen_xconfig(pid, host, port)
	gen_empty_peers()

