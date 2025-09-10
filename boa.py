import sys
import os
import shutil
import pickle
import time
import sqlite3
import xml.etree.ElementTree as ET
import cssutils
import customtkinter as ctk

class parentObj:
	def __init__(self, inter):
		self.var={}
		self.func={}
		self.inter=inter
	
	def addFunc(self, name, file):
		self.func[name]=(Interpreter(self.inter.home, self.inter.stack, True, self),file)
	
	def get(self, var):
		return self.var[var]
	
	def ret(self, v, var):
		self.var[var]=v
	
	def callFunc(self, name):
		self.func[name][0].read(self.func[name][1])

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
			data = self._d[-1]
			del self._d[-1]
			return data
		else:
			raise IndexError("You're trying to pop the stack but it's empty")

class Interpreter:

	def __init__(self, home, stack=Stack(), objFunc=False, parentObj=None):
		self.home=home
		self.cmd=None
		self.jmpPt=[]
		self.error=None
		self.var={}
		self.cursor=0
		self.code=None
		self.fctAdress={}
		self.inFct=False
		self.cond=0
		self.callAdress=None
		self.object={}
		self.stack=stack
		self.objFunc=objFunc
		self.parentObj=parentObj
		self.files=[]
	
	def executeBsql(self, file):
		with open(file) as f:
			while (l:=f.readline().replace("\n", ""))!="CLOSE":
				if (c:=l.split(" "))[0]=="OPEN":
					db = sqlite3.connect(self.home+"/"+c[1])
					cursor = db.cursor()
				elif (c:=l.split(" "))[0]=="INSERT":
					val = c[-1].split(",")
					val = [d.replace("[pop]",self.stack.pop()) if ("[pop]" in d) else d for d in val]
					c[-1]=",".join(val)
					cursor.execute(" ".join(c))
					db.commit()
				elif (c:=l.split(" "))[0] in ["SELECT","UPDATE","DELETE"]:
					c = [d.replace("[pop]",self.stack.pop()) if ("[pop]" in d) else d for d in c]
					cursor.execute(" ".join(c))
					for el in cursor.fetchone():
						self.stack.push(el)
			db.close()
	
	def parseCSS(self, file):
		sheet = cssutils.parseFile(self.home+"/"+file)
		cssData = {}
		for rule in sheet:
			propertyList = []

			for property in rule.style:
				propertyList.append((property.name,property.value))

			cssData[rule.selectorText] = propertyList
		return cssData

	def executeCSS(self, widget,tag, attrib, css):
		try:
			properties = css[tag]
			for prop in properties:
				try:
					code = f"widget.configure({prop[0]}='{prop[1]}')"
					exec(code)
				except:
					code = f"widget.configure({prop[0]}={prop[1]})"
					exec(code)
		except:
			pass
		try:
			properties = css["."+attrib["id"]]
			for prop in properties:
				try:
					code = f"widget.configure({prop[0]}='{prop[1]}')"
					exec(code)
				except:
					code = f"widget.configure({prop[0]}={prop[1]})"
					exec(code)
		except:
			pass
	
	def executeXml(self, file):
		self.xmlVar = {}
		self.xmlButton = {}
		self.xmlCheckBox = {}
		self.xmlComboBox = {}
		self.xmlOptionMenu = {}
		self.xmlRadio = {}
		self.xmlSegBtn = {}
		self.xmlSlider = {}
		self.xmlSwitch = {}
		def pos(w, p, attr):
			if p=="pack":
				try:
					expand = attr["expand"]
					if expand=="True":
						expand = True
					else:
						expand = False
				except:
					expand = False
				try:
					side = attr["side"]
				except:
					side = "top"
				w.pack(expand=expand, side=side)
			elif p=="grid":
				w.grid(column=int(attr["x"]), row=int(attr["y"]))
		def event(id, type):
			for var in self.xmlVar.values():
				if var[0]==0:
					self.stack.push(str(var[1].get()))
			int = Interpreter(self.home, self.stack)
			match type:
				case "button":
					file = self.xmlButton[id]
				case "checkbox":
					file = self.xmlCheckBox[id]
				case "combobox":
					file = self.xmlComboBox[id]
				case "optionmenu":
					file = self.xmlOptionMenu[id]
				case "radio":
					file = self.xmlRadio[id]
				case "segbtn":
					file = self.xmlSegBtn[id]
				case "slider":
					file = self.xmlSlider[id]
				case "switch":
					file = self.xmlSwitch[id]
				case _:
					file = None
			int.read(file)
			print("")
			for var in self.xmlVar.items():
				if var[1][0]==1:
					var[1][1].set(self.stack.pop())
				elif var[1][0]==2:
					var[1][1].set(int(self.stack.pop()))
		def createFrame(el, fr, p, css):
			for widget in el[:]:
				tag = widget.tag
				if tag=="label":
					attr = widget.attrib
					if attr["text"]=="{pop}":
						self.xmlVar[attr["id"]]=(1,ctk.StringVar())
						w = ctk.CTkLabel(fr, textvariable=self.xmlVar[attr["id"]][1])
					else:
						w = ctk.CTkLabel(fr, text=attr["text"])
				elif tag=="input":
					self.xmlVar[widget.attrib["id"]]=(0,ctk.StringVar())
					w = ctk.CTkEntry(fr,textvariable=self.xmlVar[widget.attrib["id"]][1])
					w.insert(0, widget.attrib["text"])
				elif tag=="button":
					self.xmlButton[widget.attrib["id"]]=widget.attrib["action"]
					w = ctk.CTkButton(fr, text=widget.attrib["text"], command=lambda c=widget.attrib["id"]: event(c, "button"))
				elif tag=="checkbox":
					self.xmlVar[widget.attrib["id"]]=(0,ctk.StringVar())
					self.xmlCheckBox[widget.attrib["id"]]=widget.attrib["action"]
					w = ctk.CTkCheckBox(fr, text=widget.attrib["text"], command=lambda c=widget.attrib["id"]: event(c, "checkbox"), variable=self.xmlVar[widget.attrib["id"]][1], onvalue=widget.attrib["on"], offvalue=widget.attrib["off"])
				elif tag=="combobox":
					self.xmlVar[widget.attrib["id"]]=(0, ctk.StringVar())
					self.xmlComboBox[widget.attrib["id"]]=widget.attrib["action"]
					w = ctk.CTkComboBox(fr, values=widget.attrib["values"].split(","), command=lambda _, c=widget.attrib["id"]: event(c, "combobox"), variable=self.xmlVar[widget.attrib["id"]][1])
				elif tag=="menu":
					self.xmlVar[widget.attrib["id"]]=(0, ctk.StringVar())
					self.xmlOptionMenu[widget.attrib["id"]]=widget.attrib["action"]
					w = ctk.CTkOptionMenu(fr, values=widget.attrib["values"].split(","), command=lambda _, c=widget.attrib["id"]: event(c, "optionmenu"), variable=self.xmlVar[widget.attrib["id"]][1])
				elif tag=="radio":
					self.xmlVar[widget.attrib["id"]]=(0, ctk.StringVar())
					self.xmlRadio[widget.attrib["id"]]=widget.attrib["action"]
					for value in widget[:]:
						button = ctk.CTkRadioButton(fr, text=value.attrib["text"], command=lambda c=widget.attrib["id"]: event(c, "radio"), variable=self.xmlVar[widget.attrib["id"]][1], value=value.attrib["value"])
						pos(button, p, widget.attrib)
					continue
				elif tag=="segbtn":
					self.xmlVar[widget.attrib["id"]]=(0, ctk.StringVar())
					self.xmlSegBtn[widget.attrib["id"]]=widget.attrib["action"]
					w = ctk.CTkSegmentedButton(fr, values=widget.attrib["values"].split(","), command=lambda _, c=widget.attrib["id"]: event(c, "segbtn"), variable=self.xmlVar[widget.attrib["id"]][1])
				elif tag=="slider":
					self.xmlVar[widget.attrib["id"]]=(0, ctk.IntVar())
					self.xmlSlider[widget.attrib["id"]]=widget.attrib["action"]
					w = ctk.CTkSlider(fr, from_=int(widget.attrib["from"]), to=int(widget.attrib["to"]), command=lambda _, c=widget.attrib["id"]: event(c, "slider"), variable=self.xmlVar[widget.attrib["id"]][1])
				elif tag=="switch":
					self.xmlVar[widget.attrib["id"]]=(0,ctk.StringVar())
					self.xmlSwitch[widget.attrib["id"]]=widget.attrib["action"]
					w = ctk.CTkSwitch(fr, text=widget.attrib["text"], command=lambda c=widget.attrib["id"]: event(c, "switch"), variable=self.xmlVar[widget.attrib["id"]][1], onvalue=widget.attrib["on"], offvalue=widget.attrib["off"])
				elif tag=="frame":
					w = ctk.CTkFrame(fr)
					createFrame(widget, w, widget.attrib["pos"], css)
				elif tag=="scroll":
					w = ctk.CTkScrollableFrame(fr)
					createFrame(widget, w, widget.attrib["pos"], css)
				pos(w,p, widget.attrib)
				self.executeCSS(w,widget.tag, widget.attrib, css)
		tree = ET.parse(file)
		root = tree.getroot()
		window = ctk.CTk()
		window.geometry(root.attrib["size"])
		window.title(root.attrib["title"])
		try:
			css = self.parseCSS(root.attrib["style"])
		except:
			css=None
		for el in root[:]:
			if el.tag=="frame":
				fr = ctk.CTkFrame(window)
			elif el.tag=="scroll":
				fr = ctk.CTkScrollableFrame(window)
			elif el.tag=="tabview":
				tabview = ctk.CTkTabview(window)
				pos(tabview, el.attrib["pos"], el.attrib)
				for tab in el[:]:
					tabview.add(tab.attrib["text"])
					createFrame(tab,tabview.tab(tab.attrib["text"]), el.attrib["pos"], css)
				break
			p = el.attrib["pos"]
			createFrame(el, fr, p, css)
			pos(fr, p, el.attrib)
		window.mainloop()

	def interprete(self, line):
		if line=="/":
			if self.cmd==7:
				if os.path.isfile(self.home+"out.bdata"):
					with open(self.home+"out.bdata", "rb") as f:
						self.stack = pickle.load(f)
				else:
					self.stack.empty()
			else:
				if len(self.jmpPt)==0:
					self.cursor=len(self.code)
				else:
					del self.jmpPt[-1]
		elif line=="":
			pass
		elif line[:2]=="//":
			pass
		elif (l:=line.split(" "))[0]=="get" and self.objFunc:
			self.var[l[1]]=self.parentObj.get(l[1])
		elif (l:=line.split(" "))[0]=="ret" and self.objFunc:
			v=l[1].split("->")
			self.parentObj.ret(self.var[v[0]], v[1])
		elif line=="}":
			if self.inFct and self.cond==0:
				self.cursor=self.callAdress
				self.inFct=False
			else:
				self.cond-=1
		elif line=="[":
			self.jmpPt.append(self.cursor)
		elif line=="]":
			if self.jmpPt==[]:
				pass
			else:
				self.cursor=self.jmpPt[-1]
		elif line[0]=="(":
			if self.cmd==3:
				if line[2]==".":
					if self.var[line[1]]!=self.var[line[3]]:
						i=self.cursor
						number=0
						while i<len(self.code):
							if len(self.code[i])>1:
								if self.code[i][-1]=="{":
									number+=1
							if self.code[i]=="}":
								number-=1
							if number==0:
								self.cursor=i
								return
							i+=1
					self.cond+=1
				elif line[2]==",":
					if self.var[line[1]]>=self.var[line[3]]:
						i=self.cursor
						number=0
						while i<len(self.code):
							if len(self.code[i])>1:
								if self.code[i][-1]=="{":
									number+=1
							if self.code[i]=="}":
								number-=1
							if number==0:
								self.cursor=i
								return
							i+=1
					self.cond+=1
				elif line[2]==";":
					if self.var[line[1]]<=self.var[line[3]]:
						i=self.cursor
						number=0
						while i<len(self.code):
							if len(self.code[i])>1:
								if self.code[i][-1]=="{":
									number+=1
							if self.code[i]=="}":
								number-=1
							if number==0:
								self.cursor=i
								return
							i+=1
					self.cond+=1
		elif line[1:]=="-$":
			if line[0]=="@":
				self.cmd=0
			elif line[0]=="#":
				self.cmd=1
			elif line[0]=="&":
				self.cmd=2
			elif line[0]=="!":
				self.cmd=3
			elif line[0]=="%":
				self.var["&"]=str(ord(input()))
			elif line[0]==":":
				self.var["&"]=input()
			elif line[0]=="/":
				self.cmd=4
			elif line[0]=="*":
				self.cmd=5
			elif line[0]=="§":
				self.cmd=6
			elif line[0]=="µ":
				self.cmd=7
			elif line[0]=="^":
				self.cmd=8
			else:
				self.error=f"[{self.cursor+1}] The Command doesn't exist"
		elif line[-1]==">" and line[0]=="<":
			file = self.files[int(line[1:-1])]
			if file[-5:]==".bsql":
				self.executeBsql(self.home+"/"+file)
			if file[-4:]==".xml":
				self.executeXml(self.home+"/"+file)
		elif line[-1]==".":
			if self.cmd==6:
				self.var[line[:-1]]=self.stack.getHead()

		elif line[-1]=="-":
			if self.cmd==4:
				self.callAdress=self.cursor
				self.cursor=self.fctAdress[line[:-1]]
				self.inFct=True
			elif self.cmd==2:
				if self.var[line[:-1]]=="128":
					print("\n", end="")
				else:
					print(chr(int(self.var[line[:-1]])), end="")
			elif self.cmd==6:
				self.stack.push(self.var[line[:-1]])
			elif self.cmd==7:
				with open(self.home+"out.bdata", "wb+") as f:
					pickle.dump(self.stack, f)
		elif line[-2]=="-":
			if self.cmd==0:
				self.var[line[-1]]=line[:-2]
			elif self.cmd==5:
				self.var[line[-1]]=self.var[line[0]]
			elif self.cmd==8:
				self.var[line[-1]]=self.createObj(self.object[line[:-2]])
		elif line[-1]=="/":
			if self.cmd==2:
				if self.var[line[:-1]]=="128":
					print("\n", end="")
				else:
					print(self.var[line[:-1]], end="")
			elif self.cmd==6:
				self.var[line[:-1]]=self.stack.pop()
		elif line[-2]==".":
			if self.cmd==1:
				try:
					self.var[line[-1]]=float(self.var[line[-1]])+float(line[:-2])
				except:
					self.var[line[-1]]=float(self.var[line[-1]])+float(self.var[line[0]])
			elif self.cmd==8:
				self.stack.push(self.var[line[-1]].get(line[:-2]))
		elif line[-2]==",":
			if self.cmd==1:
				try:
					self.var[line[-1]]=float(self.var[line[-1]])-float(line[:-2])
				except:
					self.var[line[-1]]=float(self.var[line[-1]])-float(self.var[line[0]])
		elif line[-2]==";":
			if self.cmd==1:
				try:
					self.var[line[-1]]=float(self.var[line[-1]])/float(line[:-2])
				except:
					self.var[line[-1]]=float(self.var[line[-1]])/float(self.var[line[0]])
		elif line[-2]==":":
			if self.cmd==1:
				try:
					self.var[line[-1]]=float(self.var[line[-1]])*float(line[:-2])
				except:
					self.var[line[-1]]=float(self.var[line[-1]])*float(self.var[line[0]])
		elif line[-2]=="/":
			if self.cmd==1:
				try:
					self.var[line[-1]]=float(self.var[line[-1]])**float(line[:-2])
				except:
					self.var[line[-1]]=float(self.var[line[-1]])**float(self.var[line[0]])
			elif self.cmd==8:
				self.var[line[-1]].callFunc(line[:-2])
		elif line[-2]=="\\":
			if self.cmd==1:
				try:
					self.var[line[-1]]=float(self.var[line[-1]])%float(line[:-2])
				except:
					self.var[line[-1]]=float(self.var[line[-1]])%float(self.var[line[0]])
		elif line[-2]=="+":
			if self.cmd==1:
				try:
					self.var[line[-1]]=self.var[line[-1]]+self.var[line[0]]
				except:
					self.var[line[-1]]=self.var[line[-1]]+line[:-2]
		elif line[-1]=="{":
			self.fctAdress[line[:-1]]=self.cursor
			i=self.cursor
			number=0
			while i<len(self.code):
				if len(self.code[i])>1:
					if self.code[i][-1]=="{":
						number+=1
				if self.code[i]=="}":
					number-=1
				if number==0:
					self.cursor=i
					return
				i+=1
		elif line[-1]=="$":
			print("")
			time.sleep(int(self.var[line[:-1]]))
		
	def execute(self):
		while self.cursor<len(self.code):
			self.interprete(self.code[self.cursor])
			if self.error!=None:
				print(self.error)
				return
			self.cursor+=1
	
	def createObj(self, data):
		obj=parentObj(self)
		for d in data:
			l=d.split(":")
			if l[1]=="get":
				obj.var[l[0]]=self.stack.pop()
			elif (d:=l[1].split(" "))[0]=="set":
				obj.var[l[0]]=d[1]
			else:
				obj.addFunc(l[0], l[1].replace(" ", ""))
		return obj

	def read(self, path):
		if path[-4:]==".def":
			with open(self.home+path) as f:
				definitions = f.read().split("\n")
			code=""
			if (icl:=definitions[1].split(":")[1])!="":
				include = icl.split(",")
				for el in include:
					with open(self.home+el) as f:
						code+=f.read()+"\n"
			if (obj:=definitions[2].split(":")[1])!="":
				obj = obj.split(",")
				for o in obj:
					with open(self.home+o) as f:
						data=f.read()
						data=[l.strip() for l in data.split("\n")]
						name=data[0][:-1]
						data=data[1:-1]
						self.object[name]=data
			if (files:=definitions[3].split(":")[1])!="":
				self.files = files.split(",")
			with open(self.home+definitions[0].split(":")[1]) as f:
				code+=f.read()
			self.code = code.split("\n")
			self.code = [line.strip() for line in self.code]
			self.execute()
		elif path[-2:]==".b":
			with open(self.home+path) as f:
				code = f.read()
			self.code = code.split("\n")
			self.code = [line.strip() for line in self.code]
			self.execute()
		elif path[-6:]==".bFunc":
			with open(self.home+path) as f:
				code = f.read()
			self.objFunc=True
			self.code = code.split("\n")
			self.code = [line.strip() for line in self.code]
			self.execute()
		else:
			print("This isn't the good format !")


def main(path, home):
	interpreter = Interpreter(home)
	interpreter.read(path)

if __name__=="__main__":
	arg1 = sys.argv[1]
	if arg1=="create":
		project = os.getcwd()+"/"+sys.argv[3]
		if sys.argv[2].lower()=="gui":
			shutil.copytree(sys.path[0]+"/templates/GUI", project)
		else:
			shutil.copytree(sys.path[0]+"/templates/CLI", project)
	else:
		file = sys.argv[1]
		if file[0]=="/":
			dct=""
		else:
			dct = os.getcwd()
		file=file.split("/")
		if len(file)==1:
			main(file[0], dct+"/")
		else:
			dct+="/"+"/".join(file[:-1])
			main(file[-1], dct+"/")