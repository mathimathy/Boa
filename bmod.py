import pickle
class Stack:
	def __init__(self):
		self._d = []
		
	def push(self, value):
		self._d.append(value)
		
	def pop(self):
		if len(self._d)>0:
			data = self._d[-1]
			del self._d[-1]
			return data
		else:
			raise IndexError("You're trying to pop the stack but it's empty")
	
	def empty(self):
		self._d=[]
		return None
	
	def getHead(self):
		if len(self._d)>0:
			return self._d[0]
		else:
			raise IndexError("You're trying to get the head of the stack but it's empty")

def saveStack(stack, path=""):
	with open(path+"out.bdata", "wb+") as f:
		pickle.dump(stack, f)

def loadStack(path=""):
	return pickle.load(path+"out.bdata")