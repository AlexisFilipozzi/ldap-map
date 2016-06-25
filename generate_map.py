from ldap3 import Server, Connection, ALL, SUBTREE, core
from subprocess import call
from string import Template
import re
from yaml import load
import sys
import yaml
from subprocess import call
from predicate_evaluator import PredicateEvaluator

def attribute_from_template_string(template_string):
	return re.findall(r"\$\{?(\w+)\}?", template_string)

def to_flat_dict(d):
	# generator:
	# if the input dict has a list value, we return a generator
	# on which we can iterate to get all possible dict where values are not list
	# otherwise we can iterate only on the input dict
	copy = d.copy()
	has_no_list = True
	for (key, val) in d.items():
		if isinstance(val, list):
			has_no_list = False
			for el in val:
				copy[key] = el
				yield from to_flat_dict(copy) 
			break
	if has_no_list:
		yield copy


class Bind:
	def __init__(self, name, password, addr):
		self._name = name
		self._password = password
		self._addr = addr


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


class NoAttributeException(Exception):
	def __init__(self, map_name, template):
		Exception.__init__(self,"No attribute in the current template " + str(template) + " to generate " + str(map_name))


class Generator:
	def __init__(self, filename, template, result_filter_template):
		self._map_name = filename
		self._template_string = template
		self._template = Template(self._template_string)
		self._result_filter_template_string = result_filter_template
		self._result_filter_template = Template(self._result_filter_template_string)
		self._attributes = []
		self._data = []
		self._set_attributes_from_template()

	def set_data(self, data):
		self._data = data

	def _set_attributes_from_template(self):
		match = attribute_from_template_string(self._template_string)
		if not match:
			raise NoAttributeException(self._map_name, self._template_string)
		result = match
		match_result_filter = attribute_from_template_string(self._result_filter_template_string)
		if match_result_filter:
			result += match_result_filter
		self._attributes = result

	def generate(self, postmap_cmd):
		with open(self._map_name, "w") as f:
			for entry in self._data:
				template_value = {}
				valid = True
				for flat_dict in to_flat_dict(entry):
					self.generate_for_one_entry_to_string(f, flat_dict)
		call([postmap_cmd, self._map_name])

	def generate_for_one_entry_to_string(self, f, template_value):
		try:
			# we first verify that we have to add this line
			append = True
			if self._result_filter_template_string:
				# we have to filter the result
				result_predicate = self._result_filter_template.substitute(template_value)
				evaluator = PredicateEvaluator(result_predicate)
				if not evaluator.eval_predicate():
					# the predicate is False, don't append
					append = False

			if append:
				to_append = self._template.substitute(template_value)
				f.write(str(to_append) + "\n")
		except KeyError:
			pass


class InvalidConfigurationException(Exception):
	def __init__(self, filename):
		Exception.__init__(self,"Invalid configuration file " + str(filename))



class Main:
	@staticmethod
	def main(argv):
		for arg in argv:
			Main.main_one_conf(arg)

	@staticmethod
	def main_one_conf(filename):
		conf = None
		with open(filename) as f:
			conf = yaml.load(f.read())
		if not conf:
			return
		if not Main.is_conf_valid(conf):
			raise InvalidConfigurationException(filename)

		bind = Main.get_bind(conf)
		for map_conf in conf["map"]:
			ldap_reader = LDAPReader(bind, map_conf["baseDN"], map_conf["filter"], attribute_from_template_string(map_conf["template"]))
			ldap_reader.read()
			generator = Generator(map_conf["file"], map_conf["template"], map_conf["result_filter_template"] if "result_filter_template" in map_conf else "")
			data = ldap_reader.get_list_dict_from_result()
			generator.set_data(data)
			generator.generate(conf["postmap_cmd"])
			print("file " + str(map_conf["file"]) + " has been generated")

	@staticmethod
	def get_bind(conf):
		return Bind(conf["bind"]["name"], conf["bind"]["password"], conf["bind"]["address"])

	@staticmethod
	def is_conf_valid(conf):
		if not "bind" in conf:
			return False
		if not "name" in conf["bind"]:
			return False
		if not "address" in conf["bind"]:
			return False
		if not "password" in conf["bind"]:
			return False

		if not "postmap_cmd" in conf:
			return False

		if not "map" in conf:
			return False
		for m in conf["map"]:
			if not Main.is_map_conf_valid(m):
				return False
		return True

	@staticmethod
	def is_map_conf_valid(map_conf):
		if not "file" in map_conf:
			return False
		if not "filter" in map_conf:
			return False
		if not "template" in map_conf:
			return False
		if not "baseDN" in map_conf:
			return False
		return True


if __name__ == "__main__":
	Main.main(sys.argv[1:])

