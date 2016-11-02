from subprocess import call
from typing import Any, Dict, List
from typing import Generator as typingGen
from Classes.LDAPReader import LDAPReader, LDAPReaderException
from Classes.PredicateEvaluator import PredicateEvaluator
from Classes.CheckStrategy import CheckStrategy, DiffCheckerStrategy
from Classes.FormatStrategy import FormatStrategy, DuplicateCheckStrategy, NoEmptyCheckStrategy
from Classes import TemplateFilter
from Classes.List import AutoSortList
from Classes.Mailer import Mailer
import re
import os


class NoAttributeException(Exception):
	def __init__(self, map_name: str, template: Any) -> None:
		Exception.__init__(self,"No attribute in the current template " + str(template) + " to generate " + str(map_name))

class Generator:
	def __init__(self, conf: Dict[str, Any], map_conf: Dict[str, Any]) -> None:
		self._map_conf = map_conf
		self._conf = conf
		self._files_strategies = [] # type: List[CheckStrategy]
		self._format_strategies = [] # type: List[FormatStrategy]

	@classmethod
	def create(cls, conf: Dict[str, Any], map_conf: Dict[str, Any]) -> 'Generator':
		generator = Generator(conf, map_conf)
		generator.add_format_strategy(DuplicateCheckStrategy()) # no duplicate entries
		if "check_diff" in map_conf.keys() and map_conf["check_diff"]:
			generator.add_check_strategy(DiffCheckerStrategy()) # if we have to check for diff, add this strategy
		return generator

	def smtp_conf(self)-> Dict[str, Any]:
		return self._conf["smtp"] if "smtp" in self._conf.keys() else None

	def map_conf(self) -> Dict[str, Any]:
		return self._map_conf

	def add_check_strategy(self, strat: CheckStrategy) -> None:
		self._files_strategies.append(strat)

	def add_format_strategy(self, strat: FormatStrategy) -> None:
		self._format_strategies.append(strat)

	def generate(self) -> None:
		sort_enabled = True if "sorted" not in self._map_conf else self._map_conf["sorted"]
		lines = AutoSortList(sort_enabled)
		postmap_cmd = self._conf["postmap_cmd"]

		bind = LDAPReader.create_bind(self._conf)
		for request in self._map_conf["request"]:
			attr = Generator.attribute_from_template_string(request["key_template"]) + Generator.attribute_from_template_string(request["value_template"])
			if "result_filter_template" in request:
				attr += Generator.attribute_from_template_string(request["result_filter_template"])
			ldap_reader = LDAPReader(bind, request["baseDN"], request["filter"], attr)
			try:
				ldap_reader.read()
			except LDAPReaderException as err:
				print("LDAP error: ", err)
				smtp_conf = self._conf["smtp"]
				mailer = Mailer.get_instance()
				msg = "LDAP error" + str(err)
				subject = "Trop de modification dans la génération de table Postfix"
				from_who = smtp_conf["sender"]
				to = smtp_conf["recipient"]
				smtp = smtp_conf["smtp_server"]
				
				if not mailer.send_mail(from_who, to, subject, msg, smtp):
					print("Error while sending mail")
				return # exit
			data = ldap_reader.get_list_dict_from_result()

			for entry in data:
				template_value = {} # type: Dict[str, str]
				valid = True
				for flat_dict in Generator.to_flat_dict(entry, request["keys"] if "keys" in request else None):
					line = self.generate_for_one_entry_to_string(request, flat_dict)
					if line:
						lines.add(line)

		# apply formatter
		handled_lines = [] # type: List[str]
		for line in lines.get():
			append = True
			for strat in self._format_strategies:
				if not strat.handle_line(line, handled_lines):
					append = False
					break
			if append:
				handled_lines.append(line)

		# we have generated, now we check
		force = self._conf["force"]
		for f_strat in self._files_strategies:
			if f_strat.handle_file(handled_lines, self, force) and not force: # we add and not force as a small security to be able to call all strat handle file (and thus be able to print warning)
				return

		# and we write to the file, if all checks are good
		self.write_file(handled_lines)

		call([postmap_cmd, self._map_conf["file"]])

	def write_file(self, lines: List[str]) -> Any:
		with open(self.path_of_file_to_generate(), "w") as f:
			for line in lines:
				f.write(str(line))
			print("file " + str(self._map_conf["file"]) + " has been generated")

	def path_of_file_to_generate(self) -> str:
		return self._conf["output_dir"] + os.path.sep + self._map_conf["file"]

	def generate_for_one_entry_to_string(self, request: Dict[str, Any], template_value: Dict[str, str]) -> str:
		# we first verify that we have to add this line
		append = True

		engine = TemplateFilter.Engine()

		if "result_filter_template" in request:
			result_filter_template_string = request["result_filter_template"]
			result_predicate = engine.apply(result_filter_template_string, template_value)
			# we have to filter the result
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
			key = engine.apply(request["key_template"], template_value_no_list)
			value = engine.apply(request["value_template"], template_value_no_list)
			to_append = key + "\t" + value
			return str(to_append) + "\n"
		return None

	@staticmethod
	def attribute_from_template_string(template_string: str) -> List[str]:
		return re.findall(TemplateFilter.Engine.var_filter_string_regex, template_string)

	@staticmethod
	def to_flat_dict(d, key_to_flat) -> typingGen[Dict[str, str], str, None]:
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