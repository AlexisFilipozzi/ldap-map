from Classes.CheckStrategy import DiffCheckerStrategy
from Tests.MyAssert import assertMethodIsCalled, assertMethodIsNotCalled
import unittest


class DiffCheckStrategyMock(DiffCheckerStrategy):
	def get_max_diff(self, generator: 'Generator'):
		return 2

	def send_mail(self, generator: 'Generator'):
		pass

	def get_old_file_content(self, generator: 'Generator'):
		return ["line1", "line2", "line3"]

	def old_file_exist(self, generator: 'Generator') -> bool:
		return True

	def filename(self, generator: 'Generator') -> str:
		return '/'


class DiffCheckerStrategyTest(unittest.TestCase):
	def test_generate_when_no_modif(self):
		strat = DiffCheckStrategyMock()
		self.assertFalse(strat.handle_file(["line1", "line2", "line3"], None, False))

	def test_generate_when_small_modif(self):
		strat = DiffCheckStrategyMock()
		self.assertFalse(strat.handle_file(["modif1", "line2", "line3"], None, False))

	def test_no_generate_when_too_much_modif(self):
		strat = DiffCheckStrategyMock()
		self.assertTrue(strat.handle_file(["modif1", "modif2", "line3"], None, False))

	def test_generate_when_too_much_modif_and_force(self):
		strat = DiffCheckStrategyMock()
		self.assertFalse(strat.handle_file(["modif1", "modif2", "line3"], None, True))

	def test_send_mail_when_to_much_diff(self):
		strat = DiffCheckStrategyMock()
		with assertMethodIsCalled(strat, "send_mail"):
			strat.handle_file(["modif1", "modif2", "line3"], None, False)

	def test_no_send_mail_when_to_much_diff_and_force(self):
		strat = DiffCheckStrategyMock()
		with assertMethodIsNotCalled(strat, "send_mail"):
			strat.handle_file(["modif1", "modif2", "line3"], None, True)


if __name__ == '__main__':
    unittest.main()
