import pyglet
from ui.helpers import generic_sprite, generate_batch
from config import conf
from collections import OrderedDict
from random import random

def start_game(x, y):
	print('Starting the game')
	network.send({'type' : 'server', 'action' : 'start', 'asset' : 'lobby', 'lobby_uid' : cosmic['server_id']})

def list_servers(data):
	print('Listing servers:')
	for lobby in data['result']:
		print('Lobby:', lobby)

def find_servers(x, y):
	global network
	if not network:
		network = net_class()

	network.reg_event({'action' : 'list', 'asset' : 'lobby'}, list_servers)
	network.send({'type' : 'server', 'action' : 'list', 'asset' : 'lobby'})

	print('Looking for multiplayer servers...')

def create_lobby(x, y):
	global network
	if not network:
		network = net_class()

	network.reg_event({'action' : 'create', 'asset' : 'lobby'}, open_lobby)
	network.send({'type' : 'server', 'action' : 'create', 'asset' : 'lobby', 'owner' : cosmic['pages']['multiplayer_menu']['sprites']['MP_username'].text})

def open_lobby(data):
	print('Presenting lobby:', data) # {'result': {'lobby_uid': 3459729947485851627}, 'asset': 'lobby', 'action': 'create'}

	tmp = {'batch' : None,
			'layers' : {0 : None,
						1 : None,
						2 : None,
						3 : None},
			'sprites' : {},
			'subpages' : {}}

	# == backgorund is created in the lobby object.
	#tmp['sprites']['background'] = generic_sprite, {'texture' : game_data.images[261].to_png(game_data.colorPalettes[260]), 'moveable' : False, 'clickable' : False, 'batch' : 'lobby', 'group' : 0}
	tmp['sprites']['lobby'] = lobby, {'title' : data['result']['title'], 'x' : 0, 'y' : 0, 'batch' : 'lobby', 'group' : 1}

	cosmic['server_id'] = data['result']['lobby_uid']
	cosmic['merge_pages']['lobby'] = tmp
	cosmic['active_page'] = 'lobby'

def testthing(x, y):
	print('moo')

class text_input(generic_sprite):
	def __init__(self, texture, batch=None, group=None, x=10, y=10):
		#raw_group = group
		#if type(group) == int:
		#	group = cosmic['pages'][cosmic['active_page']]['layers'][group]

		print(batch, group)
		super(text_input, self).__init__(texture, batch=batch, group=group, x=x, y=y)

		self.original_player_id = 'Player ' + str(random())[2:10]
		self.changed = True
		self.text = self.original_player_id
		#self.titleTxt = pyglet.text.Label(self.text, x=x, y=y, anchor_x='left', anchor_y='center', batch=self.batch, group=cosmic['pages'][cosmic['active_page']]['layers'][group+1] if group else None)

	def update(self):
		if self.changed:
			self.changed = False

			#if len(self.text) and self.text != self.txtLabel.text:
			if self.text != self.txtLabel.text:
				self.txtLabel.text = self.text

			if self.x != self.txtLabel.x or self.y != self.txtLabel.y:
				#self.txtLabel.x = self.x
				#self.txtLabel.y = self.y
				self.txtLabel.x=self.x+self.width/2
				self.txtLabel.y=self.y+self.height/2

	def click(self, x, y, *args, **kwargs):
		if self.text == self.original_player_id:
			self.text = ''
		elif self.text == '':
			self.text = self.original_player_id
		self.changed = True
		self.update()
		cosmic['input_to'] = self
		return True

class lobby(generic_sprite):
	def __init__(self, title='Lobby', x=0, y=0, batch=None, group=1):
		super(lobby, self).__init__(width=10, height=10, alpha=0, batch=batch)

		self.sprites['background'] = generic_sprite(game_data.images[261].to_png(game_data.colorPalettes[260]), moveable=False, clickable=False, batch=batch, group=0)
		
		self.sprites['cancel_lobby'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=self.abort_lobby, batch=batch, group=1)
		self.sprites['cancel_lobby'].x = 10
		self.sprites['cancel_lobby'].y = 10
		self.sprites['cancel_lobby'].text = 'Cancel Lobby'

		self.sprites['start_game'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=start_game, batch=batch, group=1)
		self.sprites['start_game'].x = self.sprites['cancel_lobby'].x
		self.sprites['start_game'].y = self.sprites['cancel_lobby'].y + self.sprites['cancel_lobby'].height + 10
		self.sprites['start_game'].text = 'Start Game'

		self.sprites['lobby_background'] = generic_sprite(batch=batch, width=185, height=115, group=1, alpha=128)
		self.sprites['lobby_background'].x = self.sprites['start_game'].x + self.sprites['start_game'].width + 20
		self.sprites['lobby_background'].y = self.sprites['cancel_lobby'].y

		raw_group = group
		if type(group) == int:
			group = cosmic['pages'][cosmic['active_page']]['layers'][group]


		print(title, self.sprites['lobby_background'].x+(self.sprites['lobby_background'].width/2), self.sprites['lobby_background'].y+self.sprites['lobby_background'].height-30, self.batch, cosmic['pages'][cosmic['active_page']]['layers'][raw_group+1] if group else None)
		self.titleTxt = pyglet.text.Label(title, x=self.sprites['lobby_background'].x+(self.sprites['lobby_background'].width/2), y=self.sprites['lobby_background'].y+self.sprites['lobby_background'].height-30, anchor_x='center', anchor_y='center', batch=self.batch, group=cosmic['pages'][cosmic['active_page']]['layers'][raw_group+1] if group else None)

	def update(self):
		for sName, sObj in self.sprites.items():
			sObj.update()

	def abort_lobby(self, x, y):
		cosmic['active_page'] = 'main_menu'

class main_menu(generic_sprite):
	def __init__(self, batch=None):
		super(main_menu, self).__init__(width=10, height=10, alpha=0, batch=batch)
		self.layers = OrderedDict()
		#self.layers['background'] = pyglet.graphics.OrderedGroup(0)
		#self.layers['foreground'] = pyglet.graphics.OrderedGroup(0)
		self.sprites['background'] = generic_sprite(game_data.images[261].to_png(game_data.colorPalettes[260]), moveable=False, clickable=False, group=0)
		self.main()

	def main(self, *args, **kwargs):
		cosmic['active_page'] = 'main_menu'

		self.sprites['background'].batch = cosmic['pages']['main_menu']['batch']

		self.sprites['start_game'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=start_game, batch=cosmic['pages']['main_menu']['batch'], group=1)
		self.sprites['start_game'].x = conf['resolution'].width()/2 - self.sprites['start_game'].width/2
		self.sprites['start_game'].y = conf['resolution'].height()/2 - self.sprites['start_game'].height/2 -10
		self.sprites['start_game'].text = 'Start Game'

		self.sprites['load_existing_game'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=start_game, batch=cosmic['pages']['main_menu']['batch'], group=1)
		self.sprites['load_existing_game'].x = conf['resolution'].width()/2 - self.sprites['load_existing_game'].width/2
		self.sprites['load_existing_game'].y = self.sprites['start_game'].y -50
		self.sprites['load_existing_game'].text = 'Load Game'

		self.sprites['multiplayer'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=self.multiplayer, batch=cosmic['pages']['main_menu']['batch'], group=1)
		self.sprites['multiplayer'].x = conf['resolution'].width()/2 - self.sprites['load_existing_game'].width/2
		self.sprites['multiplayer'].y = self.sprites['load_existing_game'].y -50
		self.sprites['multiplayer'].text = 'Multiplayer :D'

		self.sprites['replay_introduction'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=start_game, batch=cosmic['pages']['main_menu']['batch'], group=1)
		self.sprites['replay_introduction'].x = conf['resolution'].width()/2 - self.sprites['replay_introduction'].width/2
		self.sprites['replay_introduction'].y = self.sprites['multiplayer'].y -50
		self.sprites['replay_introduction'].text = 'Replay Introduction'

		self.sprites['quit'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=self.quit, batch=cosmic['pages']['main_menu']['batch'], group=1)
		self.sprites['quit'].x = conf['resolution'].width()/2 - self.sprites['quit'].width/2
		self.sprites['quit'].y = self.sprites['replay_introduction'].y -50
		self.sprites['quit'].text = 'Quit'
		#self.add_sprite('main_menu', 'background', generic_sprite(game_data.images[261].to_png(game_data.colorPalettes[260]), moveable=False)

	def multiplayer(self, *args, **kwargs):
		print('Pressed multiplayer! :D Lets rock!')

		if not 'multiplayer_menu' in cosmic['pages']:
			cosmic['pages']['multiplayer_menu'] = generate_batch()

		cosmic['active_page'] = 'multiplayer_menu'

		self.sprites['MP_username'] = text_input(game_data.images[239].to_png(game_data.colorPalettes[217]), batch=cosmic['pages']['multiplayer_menu']['batch'], group=1)
		self.sprites['MP_username'].x = conf['resolution'].width()/2 - self.sprites['MP_username'].width/2
		self.sprites['MP_username'].y = conf['resolution'].height()/2 #+((self.sprites['MP_username'].height+10)*3)
		#self.sprites['MP_username'].text = 'Enter a username'
		cosmic['pages']['multiplayer_menu']['sprites']['MP_username'] = self.sprites['MP_username']

		self.sprites['find_games'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=find_servers, batch=cosmic['pages']['multiplayer_menu']['batch'], group=1)
		self.sprites['find_games'].position_offset(self.sprites['MP_username'], 0, 10)
		#self.sprites['find_games'].x = conf['resolution'].width()/2 - self.sprites['find_games'].width/2
		#self.sprites['find_games'].y = conf['resolution'].height()/2
		self.sprites['find_games'].text = 'Connect to multiplayer server'
		cosmic['pages']['multiplayer_menu']['sprites']['find_games'] = self.sprites['find_games']

		self.sprites['create_multiplayer'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=create_lobby, batch=cosmic['pages']['multiplayer_menu']['batch'], group=1)
		self.sprites['create_multiplayer'].position_offset(self.sprites['find_games'], 0, 10)
		#self.sprites['create_multiplayer'].x = self.sprites['create_multiplayer'].x
		#self.sprites['create_multiplayer'].y = self.sprites['create_multiplayer'].y + self.sprites['create_multiplayer'].height + 10
		self.sprites['create_multiplayer'].text = 'Create a lobby'
		cosmic['pages']['multiplayer_menu']['sprites']['create_multiplayer'] = self.sprites['create_multiplayer']

		self.sprites['back'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=self.main, batch=cosmic['pages']['multiplayer_menu']['batch'], group=1)
		self.sprites['back'].x = conf['resolution'].width()/2 - self.sprites['back'].width/2
		self.sprites['back'].y = self.sprites['replay_introduction'].y -50
		self.sprites['back'].text = 'Back'
		cosmic['pages']['multiplayer_menu']['sprites']['back'] = self.sprites['back']

		self.sprites['background'].batch = cosmic['pages']['multiplayer_menu']['batch']

	def quit(self, *args, **kwargs):
		cosmic['quit'] = True

	def update(self):
		for sName, sObj in self.sprites.items():
			sObj.update()

class gameUI(generic_sprite):
	def __init__(self, race, batch=None):
		super(gameUI, self).__init__(width=conf['resolution'].width(), height=conf['resolution'].height(), alpha=0, batch=batch)

		self.race = race

		self.sprites['minimap'] = generic_sprite(getTexture(conf['ui'][self.race]['sidebars']['left']['minimap']['empty']), bind=start_game)
		self.sprites['minimap'].x = 0
		self.sprites['minimap'].y = conf['resolution'].height() - self.sprites['minimap'].height

		self.sprites['left_bar'] = generic_sprite(getTexture(conf['ui'][self.race]['sidebars']['left']['normal']), bind=start_game)
		self.sprites['left_bar'].x = 0
		self.sprites['left_bar'].y = conf['resolution'].height() - self.sprites['minimap'].height - self.sprites['left_bar'].height

		self.sprites['top_bar'] = generic_sprite(getTexture(conf['ui'][self.race]['sidebars']['top']['normal']), bind=start_game)
		self.sprites['top_bar'].x = self.sprites['minimap'].width
		self.sprites['top_bar'].y = conf['resolution'].height() - self.sprites['top_bar'].height

		self.sprites['right_bar'] = generic_sprite(getTexture(conf['ui'][self.race]['sidebars']['right']['normal']), bind=start_game)
		self.sprites['right_bar'].x = self.sprites['minimap'].width + self.sprites['top_bar'].width
		self.sprites['right_bar'].y = conf['resolution'].height() - self.sprites['right_bar'].height

		self.sprites['bottom_bar'] = generic_sprite(getTexture(conf['ui'][self.race]['sidebars']['bottom']['normal']), bind=start_game)
		self.sprites['bottom_bar'].x = self.sprites['minimap'].width
		self.sprites['bottom_bar'].y = 0

		# grass = tile_set 189 & 190