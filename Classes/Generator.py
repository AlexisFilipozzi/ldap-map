from string import Template
from subprocess import call
from Classes.LDAPReader import LDAPReader
from Classes.PredicateEvaluator import PredicateEvaluator
import re

class NoAttributeException(Exception):
	def __init__(self, map_name, template):
		Exception.__init__(self,"No attribute in the current template " + str(template) + " to generate " + str(map_name))

class Generator:
	def __init__(self, conf, map_conf):
		self._map_conf = map_conf
		self._conf = conf
		self._files_strategies = []

	def diff_checks(self):
		return self._conf["diff_ckeck"] if "diff_ckeck" in self._conf.keys() else None

	def map_conf(self):
		return self._map_conf

	def add_strategy(self, strat):
		self._files_strategies.append(strat)

	def generate(self, postmap_cmd):
		lines = []

		bind = LDAPReader.create_bind(self._conf)
		for request in self._map_conf["request"]:
			attr = Generator.attribute_from_template_string(request["template"])
			if "result_filter_template" in request:
				attr += Generator.attribute_from_template_string(request["result_filter_template"])
			ldap_reader = LDAPReader(bind, request["baseDN"], request["filter"], attr)
			ldap_reader.read()
			data = ldap_reader.get_list_dict_from_result()

			for entry in data:
				template_value = {}
				valid = True
				for flat_dict in Generator.to_flat_dict(entry, request["keys"] if "keys" in request else None):
					lines.append(self.generate_for_one_entry_to_string(request, flat_dict))

		# we have generated, now we check
		for strat in self._files_strategies:
			if strat.handle_file(lines, self):
				return

		# and we write to the file, if all checks are good
		self.write_file(lines)

		call([postmap_cmd, self._map_conf["file"]])

	def write_file(self, lines):
		with open(self._map_conf["file"], "w") as f:
			for line in lines:
				f.write(str(line))

	def generate_for_one_entry_to_string(self, request, template_value):
		# we first verify that we have to add this line
		append = True
		if "result_filter_template" in request:
			result_filter_template_string = request["result_filter_template"]
			result_filter_template = Template(result_filter_template_string)
			# we have to filter the result
			result_predicate = result_filter_template.substitute(template_value)
			evaluator = PredicateEvaluator(result_predicate)
			if not evaluator.eval_predicate():
				# the predicate is False, don't append
				append = False

		if append:
			template_value_no_list = {}
			for (key, val) in template_value.items():
				if isinstance(val, list):
					template_value_no_list[key] = ", ".join(val)
				else:
					template_value_no_list[key] = val
			template = Template(request["template"])
			to_append = template.substitute(template_value_no_list)
			return str(to_append) + "\n"

	@staticmethod
	def attribute_from_template_string(template_string):
		return re.findall(r"\$\{?(\w+)\}?", template_string)

	@staticmethod
	def to_flat_dict(d, key_to_flat):
		# generator:
		# if the input dict has a list value and the corresponding key is in key_to_list,
		# we return a generator on which we can iterate to get all possible dict where 
		# values are not list otherwise we can iterate only on the input dict
		#
		# if key_to_flat is None, all keys are in key_to_flat
		copy = d.copy()
		if key_to_flat is None:
			key_to_flat = list(d.keys())

		has_no_list = True
		for (key, val) in d.items():
			if key in key_to_flat:
				if isinstance(val, list):
					has_no_list = False
					for el in val:
						copy[key] = el
						yield from Generator.to_flat_dict(copy, key_to_flat) 
					break
		if has_no_list:
			yield copy