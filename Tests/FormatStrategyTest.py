from Classes.FormatStrategy import DuplicateCheckStrategy, NoEmptyCheckStrategy
import unittest

class DuplicateCheckStrategyTest(unittest.TestCase):
	def test_line_is_duplicate(self):
		strat = DuplicateCheckStrategy()
		self.assertFalse(strat.handle_line("line2", ["line1", "line2", "line3"]))

	def test_line_is_not_duplicate(self):
		strat = DuplicateCheckStrategy()
		self.assertTrue(strat.handle_line("line4", ["line1", "line2", "line3"]))


class NoEmptyCheckStrategyTest(unittest.TestCase):
	def test_recognize_empty_line(self):
		strat = NoEmptyCheckStrategy()
		self.assertFalse(strat.handle_line("", []))
		self.assertFalse(strat.handle_line(" ", []))
		self.assertFalse(strat.handle_line(" \n", []))

	def test_recognize_non_empty_line(self):
		strat = NoEmptyCheckStrategy()
		self.assertTrue(strat.handle_line("foo", []))

if __name__ == '__main__':
    unittest.main()
