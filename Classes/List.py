from typing import Any, List

class Comparator:
	def is_greater_than(self, a: Any, b: Any) -> bool:
		return a>b


class AutoSortList:
	def __init__(self, enabled: bool=True, comparator: Comparator=Comparator()) -> None:
		self._sorted = []
		self._not_sorted = []
		self._comparator = comparator
		self._enabled = enabled

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


if __name__=="__main__":
	l = AutoSortList()
	l.add(0)
	l.add(2)
	l.add(5)
	l.add(1)
	l.add(3)
	l.add(4)
	print(l.get())

	ll = AutoSortList(False)
	ll.add(2)
	ll.add(0)
	ll.add(1)
	print(ll.get())
	ll.set_enabled(True)
	print(ll.get())



