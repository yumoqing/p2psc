import os
import sys
import asyncio

class MyVOIPProtocol(asyncio.DatagramProtocol):
	def __init__(self, loop):
		self.cnt = 0
		self.loop = loop
		self.transport = None
		self.host = '127.0.0.1'
		self.port = 9999
		super().__init__()

	def send(self, msg):
		self.transport.sendto(msg)

	def connection_made(self, transport):
		print(self, 'connection_made() called')
		self.transport = transport
		self.send(b'test msg from here')

	def datagram_received(self, data, addr):
		print("Recived from: ", addr)
		if self.cnt < 10:
			self.send(data)
			self.cnt += 1
		else:
			self.loop.stop()

	def error_received(self, exc):
		print('Error received:', exc)

loop = asyncio.get_event_loop()
#loop.create_task(MyVOIPProtocol(loop).foo())
connect = loop.create_datagram_endpoint(
		lambda: MyVOIPProtocol(loop),
		remote_addr=('127.0.0.1', 9999))

loop.run_until_complete(connect)
loop.run_forever()

#transport.close()
#loop.close()
