import unittest
from Classes.TemplateFilter import Engine

class TemplateFilterTest(unittest.TestCase):
	engine = Engine()

	def test_no_filter(self):
		to_test = self.engine.apply("{{val}}", {"val": "test"})
		self.assertEqual(to_test, "test")

	def test_lower_filter(self):
		to_test = self.engine.apply("{{val || lower}}", {"val": "TEST"})
		self.assertEqual(to_test, "test")

	def test_upper_filter(self):
		to_test = self.engine.apply("{{val || upper}}", {"val": "Test"})
		self.assertEqual(to_test, "TEST")

	def test_combined_filter(self):
		to_test = self.engine.apply("{{val || lower || upper}}", {"val": "Test"})
		self.assertEqual(to_test, "TEST")


if __name__ == '__main__':
    unittest.main()