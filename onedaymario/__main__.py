import os
import sys
import pygame

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
BLOCK_SIZE = 64
H_BLOCKS = 18
V_BLOCKS = 14

JUMP_FORCE = 3
JUMP_LEN = 8

def load_sprite(img, x, y, w, h, wout=0, hout=0):
	r = pygame.Rect((x,y,x+w, x+h))
	s = pygame.Surface((w,h), pygame.SRCALPHA)
	s.blit(img, (0,0), r)
	if wout and hout:
		return pygame.transform.scale(s, (wout,hout))
	return s

class Level:

	def __init__(self):
		self.level= {}
		filename = os.path.join(ASSETS_DIR, 'level1.txt')
		self.length = 0			
		with open(filename) as f:
			for line in f:
				if len(line) < 14:
					break
				for j in range(14):
					self.level[self.length,13-j] = line[j]
				self.length += 1
		#loading sprites
		sheet = pygame.image.load(os.path.join(ASSETS_DIR, 'tile_set.png'))
		self.sprites = {
			'=' : [load_sprite(sheet, 0, 0, 16, 16, BLOCK_SIZE, BLOCK_SIZE)],
			'b' : [load_sprite(sheet, 16*13, 0, 16, 16, BLOCK_SIZE, BLOCK_SIZE)],
			'?' : [load_sprite(sheet, 16*24, 0, 16, 16, BLOCK_SIZE, BLOCK_SIZE)],
			'!' : [load_sprite(sheet, 16*24, 0, 16, 16, BLOCK_SIZE, BLOCK_SIZE)],
			'r' : [load_sprite(sheet, 0, 16*8, 32, 16, BLOCK_SIZE*2, BLOCK_SIZE)],
			'-' : [load_sprite(sheet, 0, 16*9, 32, 16, BLOCK_SIZE*2, BLOCK_SIZE)],
			'f' : [load_sprite(sheet, 16*11, 16*9, 48, 16, BLOCK_SIZE*3, BLOCK_SIZE)],
			'#' : [load_sprite(sheet, 0, 16, 16, 16, BLOCK_SIZE, BLOCK_SIZE)],
			'h' : [self.make_hill_sprite(sheet)],
		}
		self.frame=0
		self.bump = None

	def make_hill_sprite(self, sheet):
		hill = pygame.Surface((BLOCK_SIZE*3, BLOCK_SIZE*3), pygame.SRCALPHA) 
		borders = load_sprite(sheet, 16*8, 16*8,16*3,16,BLOCK_SIZE*3, BLOCK_SIZE)
		center = load_sprite(sheet, 16*8, 16*9,16,16,BLOCK_SIZE, BLOCK_SIZE)
		top = load_sprite(sheet, 16*9,16*8,16,16,BLOCK_SIZE, BLOCK_SIZE)
		hill.blit(top, (BLOCK_SIZE, 0))
		hill.blit(borders, (0, BLOCK_SIZE))
		hill.blit(center, (BLOCK_SIZE,BLOCK_SIZE))
		return hill

	def set_bump(self, block):
		if block[2] in '?!b':
			self.frame = 0
			self.bump = block

	def render(self, xoffset, surf, frame):
		startblock = xoffset // BLOCK_SIZE
		dx = xoffset - (startblock * BLOCK_SIZE)
		begin = max(0, startblock-4)
		for i in range(begin, startblock + H_BLOCKS + 1):
			for j in range(V_BLOCKS-1,-1,-1):
				b = self.level[i,j]
				x, y = ((i-startblock) * BLOCK_SIZE) -dx, j*BLOCK_SIZE
				if b in self.sprites:
					sprites = self.sprites[b]
					if self.bump and (self.bump[0], self.bump[1]) == (i,j):
						offset = 3 * self.frame if self.frame < 8 else 21 - 4*(self.frame-8)
						surf.blit(sprites[int(frame/32)%len(sprites)], (x,y - offset))
						self.frame += 1
						if self.frame > 16:
							self.bump = None
							self.frame = 0
					else:
						surf.blit(sprites[int(frame/32)%len(sprites)], (x,y))

	def block_at(self, x, y):
		k = xb, yb = x // BLOCK_SIZE, y // BLOCK_SIZE
		if k in self.level:
			b = self.level[xb, yb]
			if not b in 'f.h':
				return (xb, yb, b)
		elif x < 0:
			return (-1,yb,'#')
		elif x >= (self.length-1) * BLOCK_SIZE:
			return (self.length,yb,'#')
		return None

class Player:
	
	def __init__(self, x=0, y=0):
		self.x = x
		self.y = y
		self.vx = 0
		self.vy = 0
		self.big = True
	
		self.w = BLOCK_SIZE
		self.h = BLOCK_SIZE*2 if self.big else BLOCK_SIZE

		sheet = pygame.image.load(os.path.join(ASSETS_DIR, 'mario_bros.png'))
		self.sprites = [load_sprite(sheet, 80+16*i, 16*2, 16, 16, BLOCK_SIZE, BLOCK_SIZE) for i in range(12)]
		self.bigsprites = [load_sprite(sheet, 80+16*i, 0, 16, 32, BLOCK_SIZE, BLOCK_SIZE*2) for i in range(12)]
		self.facing = 1
		self.jumping = 0
		self.onfloor = False
		self.aniframe=0
		self.dead = False

	def render(self, surf, x, y):
		
		if self.dead:
			s = self.sprites[5]
			surf.blit(s, (x, y))
			return
		S = self.bigsprites if self.big else self.sprites
		if self.vx == 0 and self.vy == 0:
			s = S[6]
			self.aniframe = 1
		elif self.jumping > 0:
			s = S[4]
			self.aniframe = 1
		else:
			s = S[self.aniframe]
			self.aniframe += 1
			if self.aniframe == 4:
				self.aniframe = 0

		if self.facing < 0:
			s = pygame.transform.flip(s, True, False)
		surf.blit(s, (x, y))

	def blocks_around(self, level):
		top = level.block_at(self.x, self.y-1)  or level.block_at(self.x+self.w-1, self.y-1)
		bottom = level.block_at(self.x, self.y+self.h+1)  or level.block_at(self.x+self.w, self.y+self.h+1)
		left = level.block_at(self.x-1, self.y+1) or level.block_at(self.x-1, self.y + self.h-1)
		right = level.block_at(self.x+self.w+1, self.y+1) or level.block_at(self.x+self.w+1, self.y + self.h-1)
		if top:
			if right and right[1] == top[1]:right=None
			if left and left[1] == top[1]:left=None
		if bottom:
			if right and right[1] == bottom[1]:right=None
			if left and left[1] == bottom[1]:left=None
		blocks = {
			'left' : left,
			'right' : right,
			'top' : top,
			'bottom' :bottom,
		}
		
		return blocks
	

class Simulation:

	def __init__(self, size):
		self.size = size
		self.level = Level()
		self.player = Player()
		self.player.x = int(BLOCK_SIZE * 2 + BLOCK_SIZE/4)
		self.player.y = BLOCK_SIZE * 12 - self.player.h
		self.xoffset = 0
		self.frame = 0
		self.sequence = self.sequence_playing

	def scroll(self):
		l = int(self.size[0]*1/3)		
		r = int(self.size[0]*2/3)
		x = self.player.x - self.xoffset
		if x > r:
			self.xoffset += x-r
		elif x < l:
			self.xoffset += x-l
		self.xoffset = max(0, min(self.xoffset, BLOCK_SIZE * (self.level.length -H_BLOCKS-1)))

	def sequence_playing(self, buttons, elapsedMs):
		ax, ay = 0, 1
		if buttons['right']:
			ax = 2
			self.player.facing = 1
		if buttons['left']:
			ax -= 2
			self.player.facing = -1
		if buttons['jump']:
			if self.player.onfloor or self.player.jumping < JUMP_LEN:
				ay = -JUMP_FORCE
				self.player.onfloor = False
				self.player.jumping += 1

		blocks = self.player.blocks_around(self.level)

		self.player.vy = int(self.player.vy + ay)
		self.player.y += int(self.player.vy)
		self.player.vx = int(self.player.vx + ax)
		self.player.vx *= 0.95		
		self.player.x += int(self.player.vx)

		if self.player.vy < 0 and blocks['top']:
			self.player.y = (1+blocks['top'][1]) * BLOCK_SIZE + 1
			self.player.vy = - self.player.vy
			self.level.set_bump(blocks['top'])
		if self.player.vy > 0 and blocks['bottom']:
			self.player.y = blocks['bottom'][1] * BLOCK_SIZE - self.player.h - 1
			self.player.vy = 0
			self.player.jumping = 0
			self.player.onfloor = True
			
		if self.player.vx < 0 and blocks['left']:
				self.player.x = (1+blocks['left'][0]) * BLOCK_SIZE
				self.player.vx = - self.player.vx /4
			
		if self.player.vx > 0 and blocks['right']:
				self.player.x = blocks['right'][0] * BLOCK_SIZE - self.player.w - 1
				self.player.vx = - self.player.vx /4

		self.scroll()
		if self.player.y > (V_BLOCKS-1) * BLOCK_SIZE:
			self.frame = 0
			self.sequence = self.sequence_dying

	def sequence_dying(self, buttons, elapsedMs):
		if self.frame < 64:
			self.player.dead = True
			self.player.vx = 0
			self.player.vy = 0
			return
		elif self.frame == 64:
			self.player.vy = - int(BLOCK_SIZE/3)
		else:
			self.player.vy += 1
		self.player.y  += self.player.vy
		if self.player.y > (1+V_BLOCKS) * BLOCK_SIZE:
			self.sequence = self.sequence_quit;

	def sequence_quit(self, buttons, elapsedMs):
		sys.exit(0)

	def update(self, buttons, elapsedMs):
		self.sequence(buttons, elapsedMs)		
		self.frame = (self.frame + 1) % 256

	def render(self, surf):
		surf.fill((92, 148, 252))
		self.level.render(self.xoffset, surf, self.frame)
		self.player.render(surf, self.player.x - self.xoffset, self.player.y)

def main():
	pygame.init()
	screen = pygame.display.set_mode((H_BLOCKS * BLOCK_SIZE, 14 * BLOCK_SIZE))
	background = pygame.Surface(screen.get_size())  # Create empty pygame surface
	background = background.convert()  # Convert Surface to make blitting faster
	clock = pygame.time.Clock()
	milliseconds = 0
	realTime, simulationTime = 0, 0
	running = True
	font = pygame.font.SysFont('mono', 16, bold=True)
	simulation = Simulation(screen.get_size())
	buttons = {'up':0,'right':0,'down':0,'left':0,'jump':0}
	while running:
		for evt in pygame.event.get():
			if evt.type == pygame.QUIT:
				running = False
			elif evt.type in [pygame.KEYDOWN, pygame.KEYUP]:
				state = 1 if evt.type == pygame.KEYDOWN else 0
				if evt.key == pygame.K_UP:
					buttons['up'] = state
				if evt.key == pygame.K_RIGHT:
					buttons['right'] = state
				if evt.key == pygame.K_DOWN:
					buttons['down'] = state
				if evt.key == pygame.K_LEFT:
					buttons['left'] = state
				if evt.key == pygame.K_SPACE:
					buttons['jump'] = state

		realTime += clock.tick()
		while simulationTime < realTime:
			simulationTime += 16
			simulation.update(buttons, 16)

		simulation.render(background)
		surf = font.render("FPS: {:6.3}".format(clock.get_fps()), True, (0, 255, 0))
		background.blit(surf, (10,10))		
		pygame.display.flip()
		screen.blit(background, (0, 0))
	pygame.display.quit()
	pygame.quit()

main()
