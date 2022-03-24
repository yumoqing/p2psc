import asyncio
import sys


class EchoServerProtocol(asyncio.DatagramProtocol):

	def connection_made(self, transport):
		self.transport = transport
		print(self, 'connection_made()')

	def datagram_received(self, voice_msg, addr):
		print('Received voic - size: %d bytes from: %s' % (sys.getsizeof(voice_msg), addr))
		self.transport.sendto(voice_msg, addr)

loop = asyncio.get_event_loop()
print("Starting UDP server")
# One protocol instance will be created to serve all client requests
listen = loop.create_datagram_endpoint(
	EchoServerProtocol, local_addr=('127.0.0.1', 9999))
transport, protocol = loop.run_until_complete(listen)

try:
	loop.run_forever()
except KeyboardInterrupt:
	pass

transport.close()
loop.close()
