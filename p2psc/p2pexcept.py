
class UnknownPeerError(Exception):
	pass

class MissRemoteAddr(Exception):
	pass

class CRCError(Exception):
	pass

class ChannelNotReady(Exception):
	pass

class InvalidDataType(Exception):
	pass

class SignCheckError(Exception):
	pass

class StatusError(Exception):
	pass
