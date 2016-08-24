from string import Template
from subprocess import call
from Classes.PredicateEvaluator import PredicateEvaluator
import re

class NoAttributeException(Exception):
	def __init__(self, map_name, template):
		Exception.__init__(self,"No attribute in the current template " + str(template) + " to generate " + str(map_name))

class Generator:
	def __init__(self, map_conf, diff_checks):
		self._map_name = map_conf["file"]
		self._template_string = map_conf["template"]
		self._template = Template(self._template_string)
		self._result_filter_template_string = map_conf["result_filter_template"] if "result_filter_template" in map_conf else ""
		self._result_filter_template = Template(self._result_filter_template_string)
		self._data = []
		self._keys = map_conf["keys"] if "keys" in map_conf else None
		self._files_strategies = []
		self._diff_checks = diff_checks

	def diff_checks(self):
		return self._diff_checks

	def set_data(self, data):
		self._data = data

	def add_strategy(self, strat):
		self._files_strategies.append(strat)

	def generate(self, postmap_cmd):
		lines = []
		for entry in self._data:
			template_value = {}
			valid = True
			for flat_dict in Generator.to_flat_dict(entry, self._keys):
				self.generate_for_one_entry_to_string(lines, flat_dict)
		for strat in self._files_strategies:
			if strat.handle_file(lines, self):
				break
		call([postmap_cmd, self._map_name])

	def write_file(self, lines):
		with open(self._map_name, "w") as f:
			for line in lines:
				f.write(str(line))

	def generate_for_one_entry_to_string(self, lines, template_value):
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
			template_value_no_list = {}
			for (key, val) in template_value.items():
				if isinstance(val, list):
					template_value_no_list[key] = ", ".join(val)
				else:
					template_value_no_list[key] = val
			to_append = self._template.substitute(template_value_no_list)
			lines.append(str(to_append) + "\n")

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