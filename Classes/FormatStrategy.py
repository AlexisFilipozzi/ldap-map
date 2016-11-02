from typing import List

class FormatStrategy:
	# return True if the line line can be inserted, handled lines are all the line that have been inserted
	def handle_line(self, line: str, handled_lines: List[str]) -> bool:
		return True

class DuplicateCheckStrategy(FormatStrategy):
	# remove duplicate entries
	def handle_line(self, line, handled_lines):
		if line in handled_lines:
			return False
		return True


class NoEmptyCheckStrategy(FormatStrategy):
	# no line are empty
	def handle_line(self, line: str, handled_lines: List[str]) -> bool:
		strip = line.strip()
		return strip != ""