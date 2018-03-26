import pyglet
from config import conf
from collections import OrderedDict

def gen_solid_image(width, height, color='#FF0000', alpha=255):
	if type(color) == str:
		c = color.lstrip("#")
		c = max(6-len(c),0)*"0" + c
		r = int(c[:2], 16)
		g = int(c[2:4], 16)
		b = int(c[4:], 16)
	else:
		r,g,b = color
	
	c = (r,g,b,alpha)
	return pyglet.image.SolidColorImagePattern(c).create_image(width, height)

def generate_layers():
	return {0 : pyglet.graphics.OrderedGroup(0), 1 : pyglet.graphics.OrderedGroup(1), 2 : pyglet.graphics.OrderedGroup(2)}

def generate_batch():
	return {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict(), 'layers' : generate_layers(), 'subpages' : {}}

class generic_sprite(pyglet.sprite.Sprite):
	def __init__(self, texture=None, width=None, height=None, color="#C2C2C2", alpha=int(0), x=None, y=None, moveable=False, clickable=True, batch=None, group=None, bind=None):
		
		if not width:
			width = 10
		if not height:
			height = 10

		if type(texture) == str:
			if not texture or not isfile(texture):
				#print('No texutre could be loaded for sprite, generating a blank one.')
				## If no texture was supplied, we will create one
				self.texture = gen_solid_image(int(width), int(height), color, alpha)
			else:
				self.texture = pyglet.image.load(texture)

		elif texture is None:
			self.texture = gen_solid_image(int(width), int(height), color, alpha)
		else:
			self.texture = texture

		if not group:
			group = 0
		raw_group = group
		if type(group) == int:
			group = cosmic['pages'][cosmic['active_page']]['layers'][group]

		super(generic_sprite, self).__init__(self.texture, batch=batch, group=group)
		#self.batch = batch
		self.scale = conf['resolution'].scale()
		self.sprites = OrderedDict()

		if x:
			self.x = x
		else:
			self.x = 0
		if y:
			self.y = y
		else:
			self.y = 0

		#print(self.batch, self.group, self.x, self.y, self.width, self.height)
		self.text = ''
		self.txtLabel = pyglet.text.Label(self.text, x=self.x+self.width/2, y=self.y+self.height/2, anchor_x='center', anchor_y='center', batch=self.batch, group=cosmic['pages'][cosmic['active_page']]['layers'][raw_group+1] if group else None)
		#print(self.txtLabel.batch, self.txtLabel.foreground_group, self.txtLabel.x, self.txtLabel.y, self.txtLabel.width, self.txtLabel.height)

		self.moveable = moveable
		self.clickable = clickable

		if bind:
			self.click = bind
		#else:
		#	self.click = self.dummy

	def position_offset(self, obj, offset_x, offset_y, x_scale = False, y_scale = True):
		self.x = obj.x - offset_x - (obj.width if x_scale else 0)
		self.y = obj.y - offset_y - (obj.height if y_scale else 0)

	def set_batch(self, batch, group=None):
		self.batch = batch
		self.txtLabel.batch = batch
		if group:
			self.group = group
			self.txtLabel.group = group
		for sName, sObj in self.sprites.items():
			sObj.batch = batch
			if group:
				sObj.group = group

	def dummy(self, *args, **kwargs):
		pass

	def click(self, x, y):
		"""
		Usually click_check() is called followed up
		with a call to this function.
		Basically what this is, is that a click
		should occur within the object.
		Normally a class who inherits Spr() will create
		their own click() function but if none exists
		a default must be present.
		"""
		return True

	def mouse_inside(self, x, y, button=None):
		"""
		When called, we first iterate our sprites.
		If none of those returned a click, we'll
		check if we're inside ourselves.
		This is because some internal sprites might go
		outside of the object boundaries.
		"""

		for sName, sObj in self.sprites.items():
			if sObj.clickable:
				check_sObj = sObj.mouse_inside(x, y, button)
				if check_sObj:
					return check_sObj

		if self.clickable:
			if x > self.x and x < (self.x + (self.texture.width*conf['resolution'].scale())):
				if y > self.y and y < (self.y + (self.texture.height*conf['resolution'].scale())):
					return self

	def move(self, x, y):
		if self.moveable:
			self.x += x
			self.y += y
			for sprite in self.sprites:
				self.sprites[sprite].x += x
				self.sprites[sprite].y += y

	def update(self):
		if len(self.text) and self.text != self.txtLabel.text:
			self.txtLabel.text = self.text

		if self.x != self.txtLabel.x or self.y != self.txtLabel.y:
			#self.txtLabel.x = self.x
			#self.txtLabel.y = self.y
			self.txtLabel.x=self.x+self.width/2
			self.txtLabel.y=self.y+self.height/2

	def click(self, x, y):
		return True

	def _draw(self):
		self.draw()
		self.txtLabel.draw()