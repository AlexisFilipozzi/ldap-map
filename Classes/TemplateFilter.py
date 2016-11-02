import re

from typing import Dict, List, Type, Any


class InvalidFilterException(Exception):
	def __init__(self, filt: str) -> None:
		Exception.__init__(self, str(filt) + " is not a valid filter")


class NoSuchFilterException(Exception):
	def __init__(self, filter_name: str) -> None:
		Exception.__init__(self, "No such filter " + str(filter_name))


class TemplateFilter:
	def is_filter(self, name: str) -> bool:
		"""
		return True when name is the name of the filter
		"""
		return False

	def apply_filter(self, s: str) -> str:
		"""
		apply the filter on the string string
		"""
		return s


class Engine:
	_filters = [] # type: List[TemplateFilter]

	valid_template_filter_string_regex = r"\{{2}\s*(\w+)(?:\s*\|{2}\s*(\w+))*\s*\}{2}"
	template_filter_string_regex = r"\{\{[^\{\}]*\}\}"
	filter_filter_string_regex = r"\s*\|{2}\s*(\w+)"
	var_filter_string_regex = r"\{{2}\s*(\w+)\s*(?:\||\}){2}"

	@classmethod
	def add_filter(cls, filt: TemplateFilter) -> None:
		if not filt in cls._filters:
			cls._filters.append(filt)

	@classmethod
	def register_filter(cls, filt: Type[TemplateFilter]) -> Any:
		"""
		decorator to register filters
		"""
		cls.add_filter(filt())
		return cls

	def apply(self, template_string: str, values: Dict[str, str]) -> str:
		res = template_string
		template_matchs = re.findall(self.template_filter_string_regex, template_string)
		for match in template_matchs:
			# get filter, value and replace template_string by filtered value
			if not self.is_valid_template_string(match):
				raise InvalidFilterException(template_string)
			var_match = re.findall(self.var_filter_string_regex, match)
			if not var_match:
				raise InvalidFilterException(template_string)
			var_name = var_match[0]

			# get filters
			filters = re.findall(self.filter_filter_string_regex, match)
			filtered_string = self._apply_filters(values[var_name], filters)

			res = res.replace(match, filtered_string, 1)

		return res

	def is_valid_template_string(self, str: str) -> bool:
		return re.match(self.valid_template_filter_string_regex, str) is not None	

	def _apply_filters(self, string_to_filter: str, filters: List[str]) -> str:
		res = string_to_filter
		for filt in filters:
			res = self._apply_filter(res, filt)
		return res

	def _apply_filter(self, string_to_filter: str, filter_name: str) -> str:
		for f in self._filters:
			if f.is_filter(filter_name):
				return f.apply_filter(string_to_filter)
		raise NoSuchFilterException(filter_name)


@Engine.register_filter
class ToLowerCaseFilter(TemplateFilter):
	def is_filter(self, name: str) -> bool:
		return name in [ "lower_case", "lower" ]

	def apply_filter(self, string: str) -> str:
		return string.lower()


@Engine.register_filter
class ToUpperCaseFilter(TemplateFilter):
	def is_filter(self, name: str) -> bool:
		return name in [ "upper_case", "upper" ]

	def apply_filter(self, string: str) -> str:
		return string.upper()


def test(dictio):
	engine = Engine()
	for val, key in dictio.items():
		print("Test " + str(key[0]) + " -> " + str(val) + ": ", end="")
		if engine.apply(key[0], key[1]) == val:
			print("success")
		else:
			print("FAIL")

if __name__=="__main__":
	test({
			"test": ["{{val}}", {"val": "test"}],
			"test": ["{{val || lower}}", {"val": "TEST"}],
			"TEST": ["{{val || upper}}", {"val": "Test"}],
			"TEST": ["{{val || lower || upper}}", {"val": "Test"}],
		})