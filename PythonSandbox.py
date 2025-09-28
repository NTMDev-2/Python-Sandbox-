# PythonSandbox, a simple sandbox game created by NTMDev, and some help by a friend called ChatGPT. 
# Please note that due to this being a console based game, there will be update ping. Sometimes, moving will cause a lag spike and due to the lag
# the screen will be broken into multiple different section of terrian, or just corrupted generation. Press your refresh key to clear this.

fps = 50

import keyboard
import time
import os
import threading
from datetime import datetime
import random

# TODO: Fix random spawning, random chunk generation

# Session time
datetimeNOW = datetime.now()
ctime = datetimeNOW.strftime("%H:%M:%S")

GEM_SPAWN = 0.1
gemcount = 0

ispawn = True


last_dig_time = 0
dig_lock = threading.Lock()

status = ">In Game<"

debug_msg = "DEBUG SUCCESS"

def d(): # Debugging key listener
    print(debug_msg)
    return
def p(*kBUG): # Debugging output returns
    print(kBUG)
    return "Sucess"

gravity = 1

pDIG = False
isFalling = False
isJumping = False
isMoving = False

rem = set() #removed blocks
plc = set() #placed blocks
gems = set() #gems 

wMat = [] 
blocksDUG = 0

cOS = 'iOS'

# Tiles
gTILE = '#'
wsTILE = ' '
plcTILE = '@'
gemTILE = '%'
buffer = ''
player = '▇'
block = (gTILE, gemTILE, plcTILE)

if os.name == 'nt':
    cOS = 'Windows Operation System'


default = ['d', 'a', 'space', 'tab', 'f', 'k', 'g', 'r']

print("Note: To place blocks to the left or right of you, use the keybind 'n+(dir)'")
controls = list(str(input("Enter your controls in this format [right, left, jump, dig, place, debug, gems, refresh], \"Enter\" for default: ")).split())
random_seed = input("Set world seed (leave blank if none): ")
if controls == []:
    controls = default

wD, wH = 100, 10
viewD, viewH = 20, wH

camera_x, camera_y = 0, 0


ground = 3
worldDimensions = (wD, wH)

pX = int(round(wD / 2, 0))
pY = wH - ground - 1

def seed():
    seed = random.randint(0, 999999999999)
    if random_seed == '':
        random.seed(seed)
        return seed
    else:
        random.seed(random_seed)
        return random_seed

def generate_terrain(): #created by AI
    global height_variation, uSeed
    uSeed = seed()
    terrain = []
    current_height = wH - ground
    height_variation = 1

    for x in range(wD):
        current_height += random.choice([-height_variation, 0, height_variation])
        current_height = max(1, min(wH - 3, current_height))  # Keep within limits
        terrain.append(current_height)

    return terrain

globalT = generate_terrain()
def generate_chunk():
    global wMat, globalT, pX, pY
    globalT = generate_terrain() # Overlaps original terrian
    pY = wH - ground
    pX = 0
    # In development
def load_chunk():
    if pX >= wD - 1 or pX <= 0:
        generate_chunk()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def spgems():
    global gems
    gems.clear()
    for y in range(worldDimensions[1]):
        for x in range(worldDimensions[0]):
            if wMat[y][x] == gTILE:  
                if random.random() < GEM_SPAWN:
                    gems.add((x, y))
def cblocks(*block):
    count = 0
    for row in wMat:
        for cell in row:
            if cell in (block):
                count += 1
    return count
class World:
    @staticmethod
    def create():
        global wMat, pX, pY, ispawn, spawnX, spawnY
        pX = max(0, min(pX, wD - 1))
        pY = max(0, min(pY, wH - 1))

        wMat = []
        
        for y in range(worldDimensions[1]):
            row = []
            for x in range(worldDimensions[0]):
                pos = (x, y)
                if pos == (pX, pY):
                    row.append(player) # player
                elif pos in rem:
                    row.append(wsTILE)  # removed block
                elif pos in plc:
                    row.append(plcTILE)  # placed block
                elif y >= globalT[x]:
                    if pos in gems:
                        row.append(gemTILE) # gems
                    else:
                        row.append(gTILE)  # ground
                else:
                    row.append(wsTILE)  # ws (sky)
            wMat.append(row)
        wMat.append([buffer for _ in range(wD)]) # buffer
        if ispawn:
            spawnX = 0
            spawnY = 0
            while wMat[spawnY][spawnX] != wsTILE or wMat[spawnY + 1][spawnX] == wsTILE:
                spawnX = random.randint(0, wD - 1)
                spawnY = random.randint(ground, wH - 2)
            wMat[spawnY][spawnX] = player
        ispawn = False
    @staticmethod
    def draw():
        time.sleep(1 / fps)
        clear_screen()
        for row in wMat:
            print(''.join(row))
        print()
    @staticmethod
    def init():
        #World.draw_ground()
        World.create()
        World.draw()
class Player:
    @staticmethod
    def _event_right():
        global pX, pY, isMoving
        if not isFalling:
            if pX < wD - 1 and pDIG == False and wMat[pY][pX + 1] == wsTILE:
                isMoving = True
                pX += 1
                if isJumping and pY > 0 and wMat[pY - 1][pX] == wsTILE:
                    pY -= 1
                World.init()
                isMoving = False

    @staticmethod
    def _event_left():
        global pX, pY, isMoving
        if not isFalling:
            if pX > 0 and pDIG == False and wMat[pY][pX - 1] == wsTILE:
                isMoving = True
                pX -= 1
                if isJumping and pY > 0 and wMat[pY - 1][pX] == wsTILE:
                    pY -= 1
                World.init()
                isMoving = False

    @staticmethod
    def _jump():
        global pY, isJumping
        if not isFalling and pDIG == False:
            if pY > 0 and wMat[pY + 1][pX] != wsTILE and wMat[pY - 1][pX] == wsTILE:
                isJumping = True
                pY -= 1
                World.init()
                isJumping = False

    @staticmethod
    def _dig(dx, dy):
        global pX, pY, blocksDUG, last_dig_time
        if not isFalling:
            now = time.time()
            if now - last_dig_time < 0.15:
                return
            last_dig_time = now

            if dig_lock.locked():
                return

            def do_dig():
                global pX, pY, blocksDUG, gemcount
                with dig_lock:
                    tar_X = pX + dx
                    tar_Y = pY + dy

                    if 0 <= tar_X < wD and 0 <= tar_Y < wH:
                        if not wMat[tar_Y][tar_X] == buffer and \
                        (wMat[tar_Y][tar_X] == gTILE or wMat[tar_Y][tar_X] == plcTILE \
                        or wMat[tar_Y][tar_X] == gemTILE): 
                            rem.add((tar_X, tar_Y))
                            if (tar_X, tar_Y) in plc:
                                plc.remove((tar_X, tar_Y))
                            if (tar_X, tar_Y) in gems:
                                gems.remove((tar_X, tar_Y))
                                gemcount += 1
                            blocksDUG += 1
                            pX = tar_X
                            pY = tar_Y
                            World.create()
                            World.draw()

        # dig in seperate thread
        threading.Thread(target=do_dig).start()
    @staticmethod
    def _place_block(dx=0, dy=0):
        global pX, pY
        target = (pX + dx, pY + dy)
        if not isFalling:
            if 0 <= target[0] < wD and 0 <= target[1] < wH:
                if target not in plc and wMat[target[1]][target[0]] not in (buffer, gTILE):
                    plc.add(target)
                    if target in rem:
                        rem.remove(target)
                    if target == (pX, pY):
                        if pY > 0 and wMat[pY - 1][pX] == wsTILE:
                            pY -= 1
                    World.create()
                    World.draw()
    @staticmethod
    def look_gems():
        print(f"YOU HAVE {gemcount} {'GEM' if gemcount == 1 else 'GEMS'} IN YOUR INVENTORY")
    @staticmethod
    def debug():
        print(f'''
DEBUG MENU OPENED BELOW:
SESSION {ctime}
USED '{controls[5]}' TO OPEN MENU
[>==========================================================================================<]
DEBUG ITEMS BELOW:
|:==========================================================================================:|
|PLAYER X-COORDINATE: {pX}
|PLAYER Y-COORDINATE: {pY}
|CURRENT COORDINATE: {pX, pY}
|WORLD SEED: {uSeed}
|GRAVITY STRENGTH: {100 * gravity}%
|WORLD DIMENSIONS: MAXIMUM X IS [{worldDimensions[0]}], MAXIMUM Y IS [{worldDimensions[1]}]
|FULL DIMENSIONS: X-{wD}, Y-{wH}
|CONTROLS: MOVE RIGHT-{controls[0]}, MOVE LEFT-{controls[1]}, JUMP-{controls[2]}, DIG-{controls[3]}
|CONTROLS: PLACE-{controls[4]}, DEBUG-{controls[5]}, REFRESH-{controls[7]}, GEM INVENTORY-{controls[6]}
|DEFAULT CONTROLS: {str((controls == default)).upper()}
|DEBUG MESSAGE: \'{debug_msg}\'
|BLOCKS PLACED: {len(plc)}
|FPS: {fps}/50
|CURRENT MODE: PLAYER
|STATUS: {status}
|RUNNING IN: {cOS}
|NOISE DIFFERENCE: {height_variation}
|IS PLAYER DIGGING: {str(pDIG).upper()}
|IS PLAYER FALLING: {str(isFalling).upper()}
|WORLD GROUND VOLUME: {cblocks(gTILE)}
|WORLD SKY VOLUME: {cblocks(wsTILE)}
|GEMS IN WORLD: {len(gems)}
|GEM PROGRESS: {gemcount}/{len(gems)}
|GEMS SPAWN CHANCE: {int(100 * GEM_SPAWN)}%
|SPAWN COORDINATES: X-{spawnX}, Y-{spawnY}
|:==========================================================================================:|
END DEBUG ITEMS
[>==========================================================================================<]
''')

print('\033[?25l', end='') # Puts console cursor at bottom right of map
World.init()
spgems()
World.init()
print("World successfully created. Session: {}, Seed: {}".format(ctime, uSeed))

# Gravity
def _gravity():
    global pY, isFalling
    while True:
        target_y = pY + 1
        if target_y < wH:
            if wMat[target_y][pX] == wsTILE and (pX, target_y) not in plc:
                isFalling = True
                pY += 1
                World.create()
                World.draw()
            else:
                isFalling = False
        else:
            isFalling = False
        time.sleep(0.5 / gravity) # gravity speed



# Gravity Runtime
gravity_thread = threading.Thread(target=_gravity, daemon=True)
gravity_thread.start()
# Chunk Runtime
#chunk = threading.Thread(target=load_chunk,daemon=True)
#chunk.start()

# Movement
keyboard.add_hotkey(controls[0], Player._event_right)
keyboard.add_hotkey(controls[1], Player._event_left)
keyboard.add_hotkey(controls[2], Player._jump)

# Digging
keyboard.add_hotkey(controls[3], lambda: Player._dig(0, 1)) #down (default)
keyboard.add_hotkey(f"{controls[3]}+{controls[1]}", lambda: Player._dig(-1, 0)) # left
keyboard.add_hotkey(f"{controls[3]}+{controls[0]}", lambda: Player._dig(1, 0)) #right

# Block Placing
keyboard.add_hotkey(controls[4], lambda: Player._place_block(0, 0))
keyboard.add_hotkey(f"n+{controls[0]}", lambda: Player._place_block(1, 0))
keyboard.add_hotkey(f"n+{controls[1]}", lambda: Player._place_block(-1, 0))

# Debug
keyboard.add_hotkey(controls[5], Player.debug)
keyboard.add_hotkey(controls[7], World.init)

keyboard.add_hotkey(controls[6], Player.look_gems)

keyboard.wait('esc')
print("YOU LEFT THE GAME!")
status = ">Exited Game<"
print(f"Status: {status}")
time.sleep(2)
clear_screen()
print('\033[?25h', end='') # Returns console cursor

