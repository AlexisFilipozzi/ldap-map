from typing import Any, List

class Comparator:
	def is_greater_than(self, a: Any, b: Any) -> bool:
		return a>b


class AutoSortList:
	def __init__(self, enabled: bool=True, comparator: Comparator=Comparator()) -> None:
		self._sorted = [] # type: List[Any]
		self._not_sorted = [] # type: List[Any]
		self._comparator = comparator # type: Comparator
		self._enabled = enabled # type: bool

	def get(self) -> List[Any]:
		if self._enabled:
			self._sort()
			return self._sorted
		else:
			return self._sorted + self._not_sorted

	def add(self, item: Any) -> None:
		self._not_sorted.append(item)

	def _sort(self) -> None:
		self._not_sorted.sort()
		to_add_list = self._not_sorted
		self._not_sorted = []
		# to_add list is already sorted, so we only need to iterate on self._sorted one time
		i = 0
		while len(to_add_list) != 0:
			top = to_add_list.pop(0)
			while i < len(self._sorted) and self._comparator.is_greater_than(top, self._sorted[i]):
				i += 1
			self._sorted.insert(i, top)

		

	def set_enabled(self, enabled: bool) -> None:
		if enabled and not self._enabled:
			self._sort()
		self._enabled = enabled
