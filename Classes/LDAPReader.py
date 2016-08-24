from ldap3 import Server, Connection, ALL, SUBTREE, core

class LDAPReader:
	def __init__(self, bind, base_dn, query_filter, attributes):
		self._bind = bind
		self._search_scope = SUBTREE
		self._query_filter = query_filter
		self._base_DN = base_dn
		self._result = []
		self._attributes = attributes

	def read(self):
		server = Server(self._bind._addr)
		conn = Connection(server, user=self._bind._name, password=self._bind._password)
		conn.bind()
		conn.search(self._base_DN, self._query_filter, search_scope=self._search_scope, attributes=self._attributes)
		self._result = conn.entries

	def get_list_dict_from_result(self):
		result = []
		for entry in self._result:
			d = {}
			try:
				for attr in self._attributes:
					d[attr] = entry[attr].value
				result.append(d)
			except core.exceptions.LDAPKeyError as e:
				pass
		return result