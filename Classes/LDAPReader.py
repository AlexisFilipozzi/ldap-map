from ldap3 import Server, Connection, ALL, SUBTREE, core
from Classes.Bind import Bind
from typing import List, Dict, Any

class LDAPReaderException(Exception):
	def __init__(self, err: str) -> None:
		Exception.__init__(self, err)

class LDAPReader:
	def __init__(self, bind: Bind, base_dn: str, query_filter: str, attributes: List[str]) -> None:
		self._bind = bind # type: Bind
		self._search_scope = SUBTREE # type: Any
		self._query_filter = query_filter # type: str
		self._base_DN = base_dn # type: str
		self._result = [] # type: List[Any]
		self._attributes = attributes # type: List[str]

	def read(self) -> None:
		server = Server(self._bind._addr)
		conn = Connection(server, user=self._bind._name, password=self._bind._password)
		try:
			conn.bind()
			conn.search(self._base_DN, self._query_filter, search_scope=self._search_scope, attributes=self._attributes)
			self._result = conn.entries
		except core.exceptions.LDAPException as err:
			raise LDAPReaderException(err)
		

	def get_list_dict_from_result(self) -> List[Dict[str, Any]]:
		result = [] # type: List[Dict[str, Any]]
		for entry in self._result:
			d = {} # type: Dict[str, Any]
			try:
				for attr in self._attributes:
					d[attr] = entry[attr].value
				result.append(d)
			except core.exceptions.LDAPKeyError as e:
				pass
		return result

	def create_bind(conf):
		return Bind(conf["bind"]["name"], conf["bind"]["password"], conf["bind"]["address"])