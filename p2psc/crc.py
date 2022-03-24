
def gen_crc(bs):
	s = sum(bs)
	crc = s % 256
	return crc.to_bytes(1, 'big')

def check_crc(bs, crc):
	crc1 = gen_crc(bs)
	return crc1 == crc

