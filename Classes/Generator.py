from string import Template
from subprocess import call
from Classes.LDAPReader import LDAPReader
from Classes.PredicateEvaluator import PredicateEvaluator
from Classes.CheckStrategy import DiffCheckerStrategy
from Classes.FormatStrategy import DuplicateCheckStrategy, NoEmptyCheckStrategy
import re

class NoAttributeException(Exception):
	def __init__(self, map_name, template):
		Exception.__init__(self,"No attribute in the current template " + str(template) + " to generate " + str(map_name))

class Generator:
	def __init__(self, conf, map_conf, optlist):
		self._map_conf = map_conf
		self._conf = conf
		self._optlist = optlist
		self._files_strategies = []
		self._format_strategies = []

	@classmethod
	def create(cls, conf, map_conf, optlist):
		generator = Generator(conf, map_conf, optlist)
		generator.add_format_strategy(DuplicateCheckStrategy()) # no duplicate entries
		if "check_diff" in map_conf.keys() and map_conf["check_diff"]:
			generator.add_check_strategy(DiffCheckerStrategy()) # if we have to check for diff, add this strategy
		return generator

	def smtp_conf(self):
		return self._conf["smtp"] if "smtp" in self._conf.keys() else None

	def opt_list(self):
		return self._optlist

	def map_conf(self):
		return self._map_conf

	def add_check_strategy(self, strat):
		self._files_strategies.append(strat)

	def add_format_strategy(self, strat):
		self._format_strategies.append(strat)

	def generate(self):
		lines = []
		postmap_cmd = self._conf["postmap_cmd"]

		bind = LDAPReader.create_bind(self._conf)
		for request in self._map_conf["request"]:
			attr = Generator.attribute_from_template_string(request["key_template"]) + Generator.attribute_from_template_string(request["value_template"])
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

		# apply formatter
		handled_lines = []
		for line in lines:
			append = True
			for strat in self._format_strategies:
				if not strat.handle_line(line, handled_lines):
					append = False
					break
			if append:
				handled_lines.append(line)

		lines = handled_lines

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
			print("file " + str(self._map_conf["file"]) + " has been generated")

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
			# we need to remove list in template value
			# if there is a list we replace it by a string
			template_value_no_list = {}
			for (key, val) in template_value.items():
				if isinstance(val, list):
					template_value_no_list[key] = ", ".join(val)
				else:
					template_value_no_list[key] = val
			key_template = Template(request["key_template"])
			value_template = Template(request["value_template"])
			to_append = key_template.substitute(template_value_no_list) + "\t" + value_template.substitute(template_value_no_list)
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