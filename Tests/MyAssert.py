class AbstractMethodCallerChecker:
	def __init__(self, obj, method):
		self.obj = obj
		self.method = method

	def called(self, *args, **kwargs):
		self.method_called = True
		print("called")
		self.orig_method(*args, **kwargs)

	def __enter__(self):
		self.orig_method = getattr(self.obj, self.method)
		setattr(self.obj, self.method, self.called)
		self.method_called = False


class assertMethodIsCalled(AbstractMethodCallerChecker):
	def __exit__(self, exc_type, exc_value, traceback):
		assert getattr(self.obj, self.method) == self.called # check method has not changed

		print(self.method_called)
		setattr(self.obj, self.method, self.orig_method)

		# If an exception was thrown within the block, we've already failed.
		if traceback is None:
			assert self.method_called


class assertMethodIsNotCalled(AbstractMethodCallerChecker):
	def __exit__(self, exc_type, exc_value, traceback):
		assert getattr(self.obj, self.method) == self.called

		setattr(self.obj, self.method, self.orig_method)

		# If an exception was thrown within the block, we've already failed.
		if traceback is None:
			assert not self.method_called