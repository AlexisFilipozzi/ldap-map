from Classes.List import AutoSortList
import unittest

class ListTest(unittest.TestCase):
	def test_sorted(self):
		l = AutoSortList()
		l.add(0)
		l.add(2)
		l.add(5)
		l.add(1)
		l.add(3)
		l.add(4)
		self.assertEqual(l.get(), [0, 1, 2, 3, 4, 5])

	def test_not_sorted_then_sorted(self):
		l = AutoSortList(False)
		l.add(2)
		l.add(0)
		l.add(1)
		self.assertNotEqual(l.get(), [0, 1, 2])
		l.set_enabled(True)
		self.assertEqual(l.get(), [0, 1, 2])


if __name__ == '__main__':
    unittest.main()

	