#!/usr/bin/env python2

# Cupcade graphical game launcher
# Stephen Lesnick

# On cupcade this file should be run as root

import pygame, sys, ConfigParser, os
from pygame import gfxdraw
from pygame import joystick
from pygame import font
import subprocess
from subprocess import Popen
import glob
import random
import re


# number of pixels per loop when scrolling left/right
SCROLLRATE = 40

# Delay in ms before rapid scrolling if joystick held
REPEAT_DELAY = 500
# Rate of rapid scrolling after that, in ms per game
REPEAT_RATE = 75

# Time until screensaver, in seconds 
# Initial delay=after no input from user, will start randomly cycling games
# After delay=after started randomly cycling, will choose a new random game
SCREENSAVER_INITIAL_DELAY=60
SCREENSAVER_AFTER_DELAY=10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Keyboard buttons, cupcade joystick adapter
KEYUP=pygame.K_UP
KEYDOWN=pygame.K_DOWN
KEYLEFT=pygame.K_LEFT
KEYRIGHT=pygame.K_RIGHT
KEYB=pygame.K_x
KEYA=pygame.K_z
KEYSELECT=pygame.K_r
KEYSTART=pygame.K_q
KEYESC=pygame.K_ESCAPE
KEYENTER=pygame.K_RETURN

# global variable to hold current index in gameList[]
gameIndex = 0
gameCount = 0

# List of sprite images
gameList = list()

# global screen object
screen = None

# enumerated type - current state of joystick
class Direction:
	left, center, right = range(3)


# Game extends Sprite - It also adds the rom path, emu type, and alphabetical name for sorting
class Game(pygame.sprite.Sprite):
	global screen
	def __init__(self, emu, rom, img, alpha):
		pygame.sprite.Sprite.__init__(self)
		self.emu = emu
		self.rom = rom
		self.img = img
		self.alpha = alpha
		# now the Sprite stuff:
		self.image = pygame.image.load(img).convert()
		self.rect = screen.get_rect()
		self.rect.centerx = screen.get_width() / 2
		self.rect.centery = screen.get_height() / 2
		# Scale image to fill screen
		self.image = pygame.transform.scale(self.image, (screen.get_width(), screen.get_height() ))
	def set_centerx(self, centerx):
		self.rect.centerx = centerx
	def reset_centerx(self, screen):
		self.rect.centerx = screen.get_width() / 2
		
	
def main():
	global screen, gameList, gameIndex, gameCount
	# Initialize
	# PiTFT framebuffer
	os.putenv('SDL_FBDEV', '/dev/fb1')
	os.putenv('FRAMEBUFFER', '/dev/fb1')
	pygame.init()
	
	# initialize joysticks
	
	#joy = list()
	#for i in range (pygame.joystick.get_count()):
	#	joy.append(pygame.joystick.Joystick(i))
	#	joy[i].init()
	
	#AXIS = 0  # x axis
	#pygame.joystick.init()
	#joy = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
	#for joystick in joy:
	#	joystick.init()
	
	initialize_pygame_display()
	
	centerX = screen.get_width() / 2
	centerY = screen.get_height() / 2
	
	show_splash()
	
	find_roms()
	gameIndex = random.randrange(0, gameCount)
	
	# Set a recurring event every 1 second
	# once this occurs SCREENSAVER_INITIAL_DELAY times without user input,
	# will automatically scroll to random game every SCREENSAVER_AFTER_DELAY seconds. 
	pygame.time.set_timer(pygame.USEREVENT, 1000)
	screensaverCounter = 0
	screensaverActive = True
	
	muted = False
	
	# Draw the first game
	refresh_current_game()
	pygame.time.wait(100)
	
	joyPosition = Direction.center
	
	# Main loop	
	while True:
		event = pygame.event.wait()
		
		if event.type == pygame.USEREVENT:
			# Screensaver, 1 second has gone by without user interaction
			# so increment counter
			screensaverCounter += 1
			if screensaverActive == False and screensaverCounter >= SCREENSAVER_INITIAL_DELAY:
				# animate "scroll right" to random game
				gameIndex = random.randrange(0, gameCount)
				scroll_right()
				screensaverCounter = 0 # reset screensaver timer
				screensaverActive = True
			if screensaverActive == True and screensaverCounter >= SCREENSAVER_AFTER_DELAY:
				gameIndex = random.randrange(0, gameCount)
				scroll_right()
				screensaverCounter = 0 
		if event.type == pygame.KEYDOWN and (event.key == KEYA or event.key == KEYENTER):
			# Launch current game (Right Action button)
			launch_game(muted)
			screensaverCounter = 0 # user action, reset timer
			screensaverActive = False
			clear_event_queue()
		# KEYUP instead of KEYDOWN so holding Start+Select will trigger KEYESC
		elif event.type == pygame.KEYUP and event.key == KEYSELECT:
			# Toggle Mute
			muted = not muted
			if (muted):
				popup_message("Audio Muted")
			else:
				popup_message("Audio Enabled")
			screensaverCounter = 0 # user action, reset timer
			screensaverActive = False
		elif event.type == pygame.KEYUP and event.key == KEYSTART:
			# Show "About" message (START)
			show_about()
			screensaverCounter = 0 # user action, reset timer
			screensaverActive = False
			clear_event_queue()
		elif event.type == pygame.KEYDOWN and event.key == KEYLEFT:
			# scroll left then quick-scroll
			joyPosition = Direction.left
			scroll_left()
			# continue polling actively until joystick is released
			# this will allow quick scrolling after holding direction for 1 sec
			starttime = pygame.time.get_ticks()
			scrollstate = False # whether we've started fast-scrolling
			buttondepressed = True
			while (buttondepressed):
				local_event = pygame.event.poll() #clear the event queue
				# if we haven't started fast scrolling yet and 1 sec has passed
				if local_event.type == pygame.KEYUP:
					buttondepressed = False
				if scrollstate == False and pygame.time.get_ticks() > starttime + REPEAT_DELAY:
					scrollstate = True
					starttime = pygame.time.get_ticks()
				# if we're already scrolling, scroll every interval
				elif scrollstate == True and pygame.time.get_ticks() > starttime + REPEAT_RATE:
					scroll_left()
					starttime = pygame.time.get_ticks()
			screensaverCounter = 0 # user action, reset timer
			screensaverActive = False
		elif event.type == pygame.KEYDOWN and event.key == KEYRIGHT:
			# Scroll right then quick-scroll
			joyPosition = Direction.right
			scroll_right()
			# continue polling actively until joystick is released
			# this will allow quick scrolling after holding direction for 1 sec
			starttime = pygame.time.get_ticks()
			scrollstate = False  # whether we've started fast-scrolling
			buttondepressed = True
			while (buttondepressed):
				local_event = pygame.event.poll() #clear the event queue
				# if we haven't started fast scrolling yet and 1 sec has passed
				if local_event.type == pygame.KEYUP:
					buttondepressed = False
				if scrollstate == False and pygame.time.get_ticks() > starttime + REPEAT_DELAY:
					scrollstate = True
					starttime = pygame.time.get_ticks()
				# if we're already scrolling, scroll every interval
				elif scrollstate == True and pygame.time.get_ticks() > starttime + REPEAT_RATE:
					scroll_right()
					starttime = pygame.time.get_ticks()
			screensaverCounter = 0 # user action, reset timer
			screensaverActive = False
		elif event.type == pygame.KEYDOWN and event.key == KEYESC:
			# Pressed ESC, quit
			pygame.quit()
			sys.exit()




def scroll_right():
	global screen, gameList, gameIndex, gameCount
	gameIndex += 1
	if (gameIndex >= gameCount):
		gameIndex = 0
	currentGame=gameList[gameIndex]
	# slide image in from the right
	for x in range (int(screen.get_width() * 1.5), int(screen.get_width() * .5), -1 * SCROLLRATE):
		currentGame.set_centerx(x)
		render = pygame.sprite.RenderPlain(currentGame)
		render.update()
		render.draw(screen)
		pygame.display.flip()
		#pygame.time.delay(10)
	refresh_current_game()



def scroll_left():
	global screen, gameList, gameIndex, gameCount
	gameIndex -= 1
	if (gameIndex < 0):
		gameIndex = gameCount - 1
	currentGame = gameList[gameIndex]
	# slide image in from the left
	for x in range (int(screen.get_width() * -.5), int(screen.get_width() * .5), SCROLLRATE):
		currentGame.set_centerx(x)
		render = pygame.sprite.RenderPlain(currentGame)
		render.update()
		render.draw(screen)
		pygame.display.flip()
	refresh_current_game()


def clear_event_queue():
	pygame.time.wait(500)
	while (pygame.event.get()):
		pass



def show_about():
	global screen, gameList, gameIndex
	# Game(emu, rom, img, alpha)
	aboutImage = Game('', '', '/home/pi/about.png', '')
	screen.fill(BLACK)
	render = pygame.sprite.RenderPlain(aboutImage)
	render.update()
	render.draw(screen)
	pygame.display.flip()
	# Then wait for a button to be pressed to continue
	# or return after 30 seconds, using screen saver event
	finished = False
	timeoutCounter=0
	while (finished == False):
		my_event = pygame.event.wait()
		if my_event.type == pygame.KEYDOWN and my_event.key == KEYESC:
			# Pressed ESC (Start+Select held down), quit
			pygame.quit()
			sys.exit()
		elif (my_event.type == pygame.KEYDOWN):
			finished = True
		elif my_event.type == pygame.USEREVENT:
			timeoutCounter+=1
			if timeoutCounter > 30:
				finished = True
	refresh_current_game()



def popup_message(message):
	global screen
	font = pygame.font.Font(None, 36)
	text = font.render(message, True, WHITE)
	textpos = text.get_rect()
	textpos.centerx = screen.get_rect().centerx
	textpos.centery = screen.get_rect().centery
	pygame.draw.rect(screen, WHITE, (textpos.left - 15, textpos.top - 15, textpos.width + 30, textpos.height + 30))
	pygame.draw.rect(screen, BLACK, (textpos.left - 10, textpos.top - 10, textpos.width + 20, textpos.height + 20))
	screen.blit(text, textpos)
	pygame.display.flip()
	pygame.time.wait(1500)
	refresh_current_game()


def find_roms():
	global gameList, gameCount
	
	# parse list of nes roms
	nesPath='/boot/fceu/rom/'
	for romFile in glob.glob(nesPath + '*.zip'):
		# search for /boot/fceu/rom/romname.* to find matching images
		foundImage = ''
		# need to replace "[" with "[[]" because glob considers [] character classes
		for imageFile in glob.glob(romFile[:-3].replace('[', '[[]') + "*"):
			# re.I = regularexpression, case insensitive
			if bool(re.match('.*\.(gif|jpe?g|bmp|png)', imageFile, re.I)):
				foundImage = imageFile
		if not foundImage:
			print "Error: can\'t find image file for " + romFile
			pygame.quit()
			sys.exit(1)
		game = Game("NES", romFile, foundImage, os.path.basename(romFile).upper())
		gameList.append(game)
		gameCount+=1
	
	for romFile in glob.glob(nesPath + '*.nes'):
		foundImage = ''
		for imageFile in glob.glob(romFile[:-3].replace('[', '[[]') + "*"):
			if bool(re.match('.*\.(gif|jpg|bmp|png)', imageFile, re.I)):
				foundImage = imageFile
		if not foundImage:
			print "Error: can\'t find image file for " + romFile
			pygame.quit()
			sys.exit(1)
		game = Game("NES", romFile, foundImage, os.path.basename(romFile).upper())
		gameList.append(game)
		gameCount+=1
	
	# parse list of mame roms
	mamePath='/boot/advmame/rom/'
	for romFile in glob.glob(mamePath + '*.zip'):
		foundImage = ''
		for imageFile in glob.glob(romFile[:-3].replace('[', '[[]') + "*"):
			if bool(re.match('.*\.(gif|jpg|bmp|png)', imageFile, re.I)):
				foundImage = imageFile
		if not foundImage:
			print "Error: can\'t find image file for " + romFile
			pygame.quit()
			sys.exit(1)
		game = Game("ARC", romFile, foundImage, os.path.basename(romFile).upper())
		gameList.append(game)
		gameCount+=1
	
	# sort combined list into alphabetical order by rom file name
	gameList.sort(key=lambda x: x.alpha)



def launch_game(muted):
	global gameList, gameIndex, screen
	print "launching " + gameList[gameIndex].rom
	my_env=dict(os.environ) #make a copy of current environment
	
	if muted==True:
		fceuMuteCmd= '-soundvol 0'
		mameConfig= '/boot/advmame/advmame.rc.landscape.muted'
	else:
		fceuMuteCmd='-soundvol 100'
		mameConfig= '/boot/advmame/advmame.rc.landscape'
	
	if gameList[gameIndex].emu == 'ARC':
		mameRawGameName = os.path.basename(gameList[gameIndex].rom)[:-4]
		command = 'sudo FRAMEBUFFER=/dev/fb1 SDL_FBDEV=/dev/fb1 advmame -cfg ' + mameConfig + ' ' + mameRawGameName
	elif gameList[gameIndex].emu == 'NES':
		command = 'sudo FRAMEBUFFER=/dev/fb1 SDL_FBDEV=/dev/fb1 fceu ' + fceuMuteCmd + ' "' + gameList[gameIndex].rom + '"'
	
	pygame.display.quit()
	p=subprocess.Popen(command, shell=True, env=my_env)
	p.wait()
	# After game finishes
	initialize_pygame_display()
	refresh_current_game()
	clear_event_queue()


def initialize_pygame_display():
	global screen
	# Screen object
	screen = pygame.display.set_mode((320, 240), pygame.FULLSCREEN)
	pygame.mouse.set_visible(False)



# Re-draw the screen
def refresh_current_game():
	global gameList, gameIndex, screen
	screen.fill(BLACK)
	gameList[gameIndex].reset_centerx(screen)
	render = pygame.sprite.RenderPlain(gameList[gameIndex])
	render.update()
	render.draw(screen)
	pygame.display.flip()


def show_splash():
	global screen
	splashimage = Game('', '', '/home/pi/splash.png', '')
	screen.fill(BLACK)
	splashimage.reset_centerx(screen)
	render = pygame.sprite.RenderPlain(splashimage)
	render.update()
	render.draw(screen)
	pygame.display.flip()


if __name__ == "__main__":
	main()



