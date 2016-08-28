import re
import ast

def collect_offsets(call_string):
	def _abs_offset(lineno, col_offset):
		current_lineno = 0
		total = 0
		for line in call_string.splitlines():
			current_lineno += 1
			if current_lineno == lineno:
				return col_offset + total
			total += len(line)
	# parse call_string with ast
	call = ast.parse(call_string).body[0].value
	# collect offsets provided by ast
	offsets = []
	for arg in call.args:
		a = arg
		while isinstance(a, ast.BinOp):
			a = a.left
		offsets.append(_abs_offset(a.lineno, a.col_offset))
	for kw in call.keywords:
		offsets.append(_abs_offset(kw.value.lineno, kw.value.col_offset))
	if call.starargs:
		offsets.append(_abs_offset(call.starargs.lineno, call.starargs.col_offset))
	if call.kwargs:
		offsets.append(_abs_offset(call.kwargs.lineno, call.kwargs.col_offset))
	offsets.append(len(call_string))
	return offsets

def argpos(call_string):
	"""
	return position [start, end] foreach argument if we consider the string as a function
	
	raise a SyntaxError if unexpected EOF while parsing
	"""
	def _find_start(prev_end, offset):
		s = call_string[prev_end:offset]
		m = re.search('(\(|,)(\s*)(.*?)$', s)
		return prev_end + m.regs[3][0]
	def _find_end(start, next_offset):
		s = call_string[start:next_offset]
		m = re.search('(\s*)$', s[:max(s.rfind(','), s.rfind(')'))])
		return start + m.start()

	offsets = collect_offsets(call_string)   

	result = []
	# previous end
	end = 0
	# given offsets = [9, 14, 21, ...],
	# zip(offsets, offsets[1:]) returns [(9, 14), (14, 21), ...]
	for offset, next_offset in zip(offsets, offsets[1:]):
		#print 'I:', offset, next_offset
		start = _find_start(end, offset)
		end = _find_end(start, next_offset)
		#print 'R:', start, end
		result.append((start, end))
	return result


class InvalidPredicateException(Exception):
	def __init__(self, predicate):
		Exception.__init__(self, "The predicate " + str(predicate)  + "cannot be parsed")


class PredicateEvaluator:
	_strategies = []

	class PredicateValue:
		def __init__(self):
			self._eval = False

	def __init__(self, predicate):
		self._predicate = predicate

	def eval_predicate(self):
		assert(self._strategies)
		for strategy in self._strategies:
			result = PredicateEvaluator.PredicateValue()
			strat_instance = strategy()
			if strat_instance.eval(self._predicate, result):
				# the current strategy has parsed the predicate
				# no other strategy can parse this predicate
				# so the result is the on given by this strategy
				return result._eval
		raise InvalidPredicateException(self._predicate)

	@classmethod
	def register_strat(cls, strat):
		"""
		decorator to register EvaluationStrategy
		"""
		if strat not in cls._strategies:
			cls._strategies.append(strat)
		return cls


class EvaluationStrategy:
	def eval(self, predicate, evaluation_result):
		"""
		return True if there have been a match, for instance we always return 
		True when we have (and(P1)(P2)), even if P1 and P2 predicate are False

		evaluation_result is the result of the evaluation, in the case above, it's 
		True only when P1 and P2 are true
		"""
		return False

	@staticmethod
	def get_sub_predicates(pred):
		positions = argpos(pred)
		result = []
		for pos in positions:
			result.append(pred[pos[0]:pos[1]])
		return result

	@staticmethod
	def get_unquoted_arg(arg):
		if arg[0]  == arg[-1] == "'":
			return arg[1:-1]

		if arg[0] == arg[-1] == "\"":
			return arg[1:-1]
		return arg


@PredicateEvaluator.register_strat
class AndEvaluationStrategy(EvaluationStrategy):
	def eval(self, predicate, evaluation_result):
		outer_match = re.findall(r"^and_l\((.+)\)$", predicate)
		if outer_match:
			inners_predicate = self.get_sub_predicates(predicate)
			if inners_predicate:
				evaluation_result._eval = True
				for pred in inners_predicate:
					evaluator = PredicateEvaluator(pred)
					if not evaluator.eval_predicate():
						evaluation_result._eval = False
						# we don't need to go further
						return True
			return True
		return False


@PredicateEvaluator.register_strat
class OrEvaluationStrategy(EvaluationStrategy):
	def eval(self, predicate, evaluation_result):
		outer_match = re.findall(r"^or_l\((.+)\)$", predicate)
		if outer_match:
			inners_predicate = self.get_sub_predicates(predicate)
			if inners_predicate:
				evaluation_result._eval = False
				for pred in inners_predicate:
					evaluator = PredicateEvaluator(pred)
					if evaluator.eval_predicate():
						evaluation_result._eval = True
						# we don't need to go further
						return True
			return True
		return False


@PredicateEvaluator.register_strat
class NotEvaluationStrategy(EvaluationStrategy):
	def eval(self, predicate, evaluation_result):
		outer_match = re.findall(r"^not_p\((.+)\)$", predicate)
		if outer_match:
			inner = outer_match[0]
			evaluator = PredicateEvaluator(inner)
			evaluation_result._eval = (not evaluator.eval_predicate())
			return True
		return False


@PredicateEvaluator.register_strat
class ContainEvaluationStrategy(EvaluationStrategy):
	def eval(self, predicate, evaluation_result):
		"""
			the predicate is :
			contains(s, s0, s1, ...), it is true if s contains s0, s1, ...
			false otherwise
		"""
		outer_match = re.findall(r"^contains\((.+)\)$", predicate)
		if outer_match:
			inner = outer_match[0]
			args = self.get_sub_predicates(predicate)
			if len(args) >= 2:
				evaluation_result._eval = True
				for sub_str in args[1:]:
					unquoted_sub_str = self.get_unquoted_arg(sub_str)
					unq_str = self.get_unquoted_arg(args[0])
					if unquoted_sub_str not in unq_str:
						evaluation_result._eval = False
						# the string doesn't contains one of the other argument
						# we don't need to go further
						return True
			return True
		return False


@PredicateEvaluator.register_strat
class EqualEvaluationStrategy(EvaluationStrategy):
	def eval(self, predicate, evaluation_result):
		"""
			the predicate is :
			equal(s, s0, s1, ...), it is true if s equal to s0 and  s1 and ...
			false otherwise
		"""
		outer_match = re.findall(r"^equals\((.+)\)$", predicate)
		if outer_match:
			inner = outer_match[0]
			args = self.get_sub_predicates(predicate)
			if len(args) >= 2:
				evaluation_result._eval = True
				for sub_str in args[1:]:
					unquoted_sub_str = self.get_unquoted_arg(sub_str)
					unq_str = self.get_unquoted_arg(args[0])
					if unquoted_sub_str != unq_str:
						evaluation_result._eval = False
						# we don't need to go further
						return True
			return True
		return False


if __name__=="__main__":
	def test(dict):
		success_count = 0
		for (key, val) in dict.items():
			print("Test \"" + key + "\": ", end="")
			evaluator = PredicateEvaluator(key)
			if evaluator.eval_predicate() == val:
				success_count += 1
				print("success")
			else:
				print("FAIL")

		print("Nb of tests: " + str(len(dict)) + ", success: " + str(success_count) + ", fail: " + str(len(dict) - success_count))

	tests = {
		"contains(aaa, 'aa')": True,
		"contains(aaa, 'b b')": False,
		"not_p(contains(aaa, b))": True,
		"or_l(contains(aaa, a), contains(aaa, b))": True,
		"or_l(contains(aaa, b), contains(aaa, a))": True,
		"or_l(contains(aaa, c), contains(aaa, b))": False,
		"and_l(contains(aba, ba), contains(aba, a))": True,
		"and_l(contains(aba, ba), contains(aba, c))": False,
		"equals(aaa, aaa)": True,
		"equals(aaa, aa)": False,
		"contains('testuser@example.com', '@example.com')": True,
	}
	test(tests)
