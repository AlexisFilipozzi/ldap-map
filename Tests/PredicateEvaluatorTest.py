from Classes.PredicateEvaluator import PredicateEvaluator
import unittest

class PredicateEvaluatorTest(unittest.TestCase):
	def test_contains_true(self):
		evaluator = PredicateEvaluator("contains(aaa, 'aa')")
		self.assertTrue(evaluator.eval_predicate())

	def test_contains_false(self):
		evaluator = PredicateEvaluator("contains(aaa, 'b b')")
		self.assertFalse(evaluator.eval_predicate())

	def test_not(self):
		evaluator = PredicateEvaluator("not_p(contains(aaa, b))")
		self.assertTrue(evaluator.eval_predicate())

	def test_or_left_true(self):
		evaluator = PredicateEvaluator("or_l(contains(aaa, a), contains(aaa, b))")
		self.assertTrue(evaluator.eval_predicate())

	def test_or_right_true(self):
		evaluator = PredicateEvaluator("or_l(contains(aaa, b), contains(aaa, a))")
		self.assertTrue(evaluator.eval_predicate())

	def test_or_false(self):
		evaluator = PredicateEvaluator("or_l(contains(aaa, c), contains(aaa, b))")
		self.assertFalse(evaluator.eval_predicate())

	def test_and_true(self):
		evaluator = PredicateEvaluator("and_l(contains(aba, ba), contains(aba, a))")
		self.assertTrue(evaluator.eval_predicate())

	def test_and_false(self):
		evaluator = PredicateEvaluator("and_l(contains(aba, ba), contains(aba, c))")
		self.assertFalse(evaluator.eval_predicate())

	def test_equal_true(self):
		evaluator = PredicateEvaluator("equals(aaa, aaa)")
		self.assertTrue(evaluator.eval_predicate())

	def test_equal_false(self):
		evaluator = PredicateEvaluator("equals(aaa, aa)")
		self.assertFalse(evaluator.eval_predicate())

	def test_contains_mail_true(self):
		evaluator = PredicateEvaluator("contains('testuser@example.com', '@example.com')")
		self.assertTrue(evaluator.eval_predicate())


if __name__ == '__main__':
    unittest.main()
