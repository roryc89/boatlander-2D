#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
author: Rory Campbell
made using sections of code from thepythongamebook
licence: gpl, see http://www.gnu.org/licenses/gpl.html

"""
def game(folder = "data"):
    import pygame
    import os
    import random
    import math
    import sys
    #------ starting pygame -------------
    pygame.mixer.pre_init(44100, -16, 2, 2048) # setup mixer to avoid sound lag
    pygame.init()
    screen=pygame.display.set_mode((1200,850)) # try out larger values and see what happens !
    screenrect = screen.get_rect()

    rock_dist = 0.07 * screenrect[3]
    slip_len = 0.235 * screenrect[3]
    l_shal = 0.515 * screenrect[2]
    r_shal =  0.745 * screenrect[2]
    l_trail = (float(354)/float(640)) * screenrect[2]
    r_trail = (float(389)/float(640)) * screenrect[2]
    trail_len = (float(136)/float(480)) * screenrect[3]

    
    #winstyle = 0  # |FULLSCREEN # Set the display mode
    #print "pygame version", pygame.ver 
    # ------- game constants ----------------------
    GRAD = math.pi / 180 # 2 * pi / 360   # math module needs Radiant instead of Grad
    # ----------- functions -----------
    def write(msg=">>>>>>", color=(255,255,255)):
        """write text into pygame surfaces"""
        myfont = pygame.font.SysFont("None", 32)
        mytext = myfont.render(msg, True, color)
        #mytext = mytext.convert_alpha()
        return mytext
        
    def getclassname(class_instance):
        """this function extract the class name of a class instance.
        For an instance of a XWing class, it will return 'XWing'."""
        text = str(class_instance.__class__) # like "<class '__main__.XWing'>"
        parts = text.split(".") # like ["<class '__main__","XWing'>"]
        return parts[-1][0:-2] # from the last (-1) part, take all but the last 2 chars
    
    def radians_to_degrees(radians):
        return (radians / math.pi) * 180.0
    
    def degrees_to_radians(degrees):
        return degrees * (math.pi / 180.0)
    
    def elastic_collision(sprite1, sprite2):
        """elasitc collision between 2 sprites (calculated as disc's).
           The function alters the dx and dy movement vectors of both sprites.
           The sprites need the property .mass, .radius, .pos[0], .pos[1], .dx, dy
           pos[0] is the x postion, pos[1] the y position"""
        # here we do some physics: the elastic
        # collision
        # first we get the direction of the push.
        # Let's assume that the sprites are disk
        # shaped, so the direction of the force is
        # the direction of the distance.
        dirx = sprite1.pos[0] - sprite2.pos[0]
        diry = sprite1.pos[1] - sprite2.pos[1]
        # the velocity of the centre of mass
        sumofmasses = sprite1.mass + sprite2.mass
        sx = (sprite1.dx * sprite1.mass + sprite2.dx * sprite2.mass) / sumofmasses
        sy = (sprite1.dy * sprite1.mass + sprite2.dy * sprite2.mass) / sumofmasses
        # if we sutract the velocity of the centre
        # of mass from the velocity of the sprite,
        # we get it's velocity relative to the
        # centre of mass. And relative to the
        # centre of mass, it looks just like the
        # sprite is hitting a mirror.
        bdxs = sprite2.dx - sx
        bdys = sprite2.dy - sy
        cbdxs = sprite1.dx - sx
        cbdys = sprite1.dy - sy
        # (dirx,diry) is perpendicular to the mirror
        # surface. We use the dot product to
        # project to that direction.
        distancesquare = dirx * dirx + diry * diry
        if distancesquare == 0:
            # no distance? this should not happen,
            # but just in case, we choose a random
            # direction
            dirx = random.randint(0,11) - 5.5
            diry = random.randint(0,11) - 5.5
            distancesquare = dirx * dirx + diry * diry
        dp = (bdxs * dirx + bdys * diry) # scalar product
        dp /= distancesquare # divide by distance * distance.
        cdp = (cbdxs * dirx + cbdys * diry)
        cdp /= distancesquare
        # We are done. (dirx * dp, diry * dp) is
        # the projection of the velocity
        # perpendicular to the virtual mirror
        # surface. Subtract it twice to get the
        # new direction.
        # Only collide if the sprites are moving
        # towards each other: dp > 0
        if dp > 0:
            sprite2.dx -= 2 * dirx * dp 
            sprite2.dy -= 2 * diry * dp
            sprite1.dx -= 2 * dirx * cdp 
            sprite1.dy -= 2 * diry * cdp
    
    # ----------- classes ------------------------

    class Text(pygame.sprite.Sprite):
        """a pygame Sprite displaying text"""
        def __init__(self, msg="", color=(0,0,0), topleft=(0,0)):
            self.groups = allgroup
            self.topleft = topleft
            self._layer = 1
            pygame.sprite.Sprite.__init__(self, self.groups)
            self.newmsg(msg,color)
            
        def update(self, time):
            pass # allgroup sprites need update method that accept time
        
        def newmsg(self, msg, color=(255,255,0)):
            self.image =  write(msg,color)
            self.rect = self.image.get_rect()
            self.rect.topleft = self.topleft

    class GameObject(pygame.sprite.Sprite):
        """generic Game Object Sprite class, to be called from every Sprite
           with a physic collision (Player, Rocket, Monster, Bullet)
           need self.image and self.image0 and self.groups to be set
           need self.rect and self.pos to be set
           self.hitpoints must be set to a float, also self.hitpointsfull"""
        image=[]  # list of all images
        gameobjects = {} # a dictionary of all GameObjects, each GameObject has its own number
        number = 0
        crashed = False
        landed = False  
        #def __init__(self, pos, layer= 4, area=screenrect, areastop = False, areabounce = False, angle=0, speedmax = 500, friction = 0.95, lifetime = -1):
        def __init__(self, layer= 4, area=screenrect, areastop = False, areabounce = False, angle=0, speedmax = 500, friction = 0.95, lifetime = -1):
            #self.pos = pos
            self._layer = layer                   # assign level
            self.area = area
            self.areastop = areastop
            self.areabounce = areabounce
            self.angle = angle 
            self.crashed = False
            self.landed = False            
            self.oldangle = angle
            self.speedmax = speedmax
            self.friction = friction # between 0 and 1, 1 means no friction, 0 means no more movement is possible
            self.lifetime = lifetime # -1 means infinite lifetime
            pygame.sprite.Sprite.__init__(self,  self.groups  ) #---------------call parent class. NEVER FORGET !
            self.alivetime = 0.0 # how long does this GameObjectexist ?
            self.bouncefriction = -0.5 # how much speed is lost by bouncing off a wall. 1 means no loss, 0 means full stop
            self.dx = 0   # wait at the beginning
            self.dy = 0            
            self.number = GameObject.number # get my personal GameObject number
            GameObject.number+= 1           # increase the number for next GameObject
            GameObject.gameobjects[self.number] = self # store myself into the GameObject dictionary
          
        def speedcheck(self):
            speed = (self.dx**2 + self.dy**2)**0.5 ## calculate total speed
            if speed > self.speedmax:
                factor = self.speedmax / speed * 1.0
                self.dx *= factor
                self.dy *= factor
            #----------- friction -------------            
            if abs(self.dx) > 0 : 
                self.dx *= self.friction  # make the Sprite slower over time
            if abs(self.dy) > 0 :
                self.dy *= self.friction

        def areacheck(self):
            """if GameObject leave self.arena, it is bounced (self.areabounce) or stopped (self.areastop)"""
            """possibility of changing bouncing to death and changing top y limit to include shore"""
            #if (self.areastop or self.areabounce) and not self.area.contains(self.rect):
                # --- compare self.rect and area.rect
            if self.pos[0] + self.rect.width/2 > self.area.right:
                self.pos[0] = self.area.right - self.rect.width/2
                if self.areabounce:
                    self.dx *= self.bouncefriction # bouncing off but loosing speed
                else:
                    self.dx = 0
            if self.pos[0] - self.rect.width/2 < self.area.left:
                self.pos[0] = self.area.left + self.rect.width/2                
                if self.areabounce:
                    self.dx *= self.bouncefriction # bouncing off but loosing speed
                else:
                    self.dx = 0
            if self.pos[1] + self.rect.height/2 > self.area.bottom:
                self.pos[1] = self.area.bottom - self.rect.height/2                
                if self.areabounce:
                    self.dy *= self.bouncefriction # bouncing off but loosing speedd
                else:
                    self.dy = 0
            if self.pos[1] - self.rect.height/2 < self.area.top + rock_dist:
                self.pos[1] = (self.area.top + rock_dist) + self.rect.height/2
                GameObject.crashed = True
                self.dx = 0 
                self.dy = 0
                current = 0                
                if self.areabounce:
                    self.dy *= self.bouncefriction # bouncing off but loosing speed
            if self.pos[1] - self.rect.height/2 < self.area.top + slip_len and self.area.left + r_shal > self.pos[0] + self.rect.width/2 > self.area.left + l_shal:
                self.dx = 0 
                self.dy = 0
                current = 0 
                GameObject.crashed = True
            if self.pos[1] - self.rect.height/2 < self.area.top + trail_len and (self.area.left + l_trail * .99 < self.pos[0] + self.rect.width/2 < self.area.left + l_trail * 1.01 or self.area.left + r_trail * 99 < self.pos[0] + self.rect.width/2 < self.area.left + r_trail * 1.01):
                self.dx = 0 
                self.dy = 0
                current = 0 
                GameObject.crashed = True
            if self.pos[1] - self.rect.height/2 < self.area.top + trail_len and self.area.left + l_trail < self.pos[0] + self.rect.width/2 < self.area.left + r_trail:
                if self.pos[1] - self.rect.height/2 < self.area.top + (slip_len * 1.05) and self.area.left + l_trail < self.pos[0] + self.rect.width/2 < self.area.left + r_trail:
                    self.dx = 0 
                    self.dy = 0
                    current = 0
                    if self.dx < 10 and self.dy < 20 and self.angle % 360 < 10:
                        GameObject.landed = True 
                        GameObject.crashed = True
                        self.dx = 0 
                        self.dy = 0
                        current = 0                                     
                    else:
                        GameObject.crashed = True
                        self.dx = 0 
                        self.dy = 0
                        current = 0                         
                else:
                    if self.dx > 10 and self.dy > 20 and self.angle % 360 > 10:
                        GameObject.crashed = True
                        self.dx = 0 
                        self.dy = 0
                        current = 0 

                        
        def rotate_toward_moving(self, dx= None, dy=None):
            if dx is None and dy is None:
                dx = self.dx
                dy = self.dy
            return  math.atan2(-dx, -dy)/math.pi*180.0 
        
        def kill(self):
            GameObject.gameobjects[self.number] =   None # delete sprite from dictionary
            pygame.sprite.Sprite.kill(self) # kill the sprite              
        
        def update(self, seconds):
            self.alivetime += seconds
            # --------- rotated ? -------------------
            if self.angle != self.oldangle:            
                self.oldcenter = self.rect.center
                self.image = pygame.transform.rotate(self.image0, self.angle)
                self.rect = self.image.get_rect()
                self.rect.center = self.oldcenter
                self.oldangle = self.angle

            #----------moving ----------------
            self.pos[0] += self.dx * seconds
            self.pos[1] += self.dy * seconds
            self.speedcheck()    # ------------- movement
            self.areacheck() # ------- check if boat out of screen
            self.rect.centerx = round(self.pos[0],0)
            self.rect.centery = round(self.pos[1],0)
    
    class Trailerleg(GameObject):
        def __init__(self):
            pass




    class Player(GameObject):
        """a class to hold all players"""
        current = 0
        number = 0
        image = []
        def __init__(self, playernumber = 0):
            self.playernumber = Player.number
            Player.number += 1 # prepare number for next player 
            self.image = Player.image[self.playernumber] # start with 0
            self.image0 = Player.image[self.playernumber] # start with 0 
            self.rect = self.image.get_rect()
            self.mask = pygame.mask.from_surface(self.image) # pixelmask ---- necessary ?
            self.pos = [screen.get_width()/10*2,screen.get_height()-30]
            self.angle = 270
            # ---------- both players ---------
            self.groups = allgroup, playergroup, gravitygroup
            #  def __init__(self, pos, layer= 4, area=screenrect, areastop = False, areabounce = False, angle=0, speedmax = 500, friction = 0.8, lifetime = -1)
            GameObject.__init__(self, areastop = True, angle = self.angle, speedmax = 300) # ------------------- important ! ----------------------
            self.speed = 10.0 # base movement speed factor
            self.rotatespeed = 2.0 # rotating speed
            self.frags = 100
            self.cooldowntime = 0.08 #seconds
            self.cooldown = 0.0
            self.mass = 400.0
            self.frags = 100
            self.oldangle = -5
            
        def kill(self):
            bombsound.play()
            for _ in range(self.frags):
                RedFragment(self.pos)
            GameObject.kill(self) # call parent method           
        
        def update(self, seconds):
            pressedkeys = pygame.key.get_pressed()
            self.ddx = 0.0
            self.ddy = 0.0
            if crash == False:
                if pressedkeys[pygame.K_w]: # forward
                        self.ddx = -math.sin(self.angle*GRAD) 
                        self.ddy = -math.cos(self.angle*GRAD) 
                        Wake((self.rect.center[0]-(self.ddx * 45),self.rect.center[1]-(self.ddy * 45)), -self.ddx , -self.ddy)
                        Wake((self.rect.center[0]-(self.ddx * 45),self.rect.center[1]-(self.ddy * 45)), -self.ddx , -self.ddy)
                        Wake((self.rect.center[0]-(self.ddx * 45),self.rect.center[1]-(self.ddy * 45)), -self.ddx , -self.ddy)
                if pressedkeys[pygame.K_s]: # backward
                        self.ddx = +math.sin(self.angle*GRAD)/3
                        self.ddy = +math.cos(self.angle*GRAD)/3 
                        Wake(self.rect.center, -self.ddx, -self.ddy)

                   
                #-------------rotate----------------
                if pressedkeys[pygame.K_a]: # left turn , counterclockwise
                    self.angle += self.rotatespeed
                if pressedkeys[pygame.K_d]: # right turn, clockwise
                    self.angle -= self.rotatespeed
                if pressedkeys[pygame.K_o] and Player.current > -30:
                    Player.current -= 1
                    #background.blit(write("current = " + str(self.current), (200,200,200)),(0,0))
                if pressedkeys[pygame.K_p] and Player.current < 30:
                    Player.current += 1
                    #background.blit(write("current = " + str(self.current), (200,200,200)),(0,0))


              # ------------move------------------
            self.dx += self.ddx * self.speed + (self.current * 0.2)
            self.dy += self.ddy * self.speed
              # ----- move, rotate etc. ------------  
            GameObject.update(self, seconds)# ------- call parent function
            #print self.dx
            #print self.dy
            #print self.angle   
             

    class Fragment(pygame.sprite.Sprite):
        """generic Fragment class. """
        number = 0
        def __init__(self, pos, layer = 9):
            self._layer = layer
            pygame.sprite.Sprite.__init__(self, self.groups)
            self.pos = [0.0,0.0]
            self.fragmentmaxspeed = 200# try out other factors !
            self.number = Fragment.number
            Fragment.number += 1
            
        def init2(self):  # split the init method into 2 parts for better access from subclasses
            self.image = pygame.Surface((10,10))
            self.image.set_colorkey((0,0,0)) # black transparent
            self.fragmentradius = random.randint(2,5)
            pygame.draw.circle(self.image, self.color, (5,5), self.fragmentradius)
            self.image = self.image.convert_alpha()
            self.rect = self.image.get_rect()
            self.rect.center = self.pos #if you forget this line the sprite sit in the topleft corner
            self.time = 0.0
            
        def update(self, seconds):
            self.time += seconds
            if self.time > self.lifetime:
                self.kill()
            if self.pos[1] < rock_dist * 1.1:
                self.kill()
            if self.pos[1] < slip_len and l_shal * .96 < self.pos[0] < r_shal * .93:
                self.kill()

            self.pos[0] += self.dx * seconds
            self.pos[1] += self.dy * seconds
            self.rect.centerx = round(self.pos[0],0)
            self.rect.centery = round(self.pos[1],0)
            
            
    class Wake(Fragment):
        """white disturbed water indicating that the sprite is moved.
           Wake direction is inverse of players movement direction"""
        def __init__(self, pos, dx, dy, colmin=200, colmax=255):
           self.color = ( random.randint(colmin,colmax), random.randint(colmin,colmax), random.randint(colmin,colmax))
           self.groups = allgroup
           Fragment.__init__(self,pos, 3) # give startpos and layer 
           self.pos[0] = pos[0] 
           self.pos[1] = pos[1]
           self.lifetime = 2.5 + random.random()*3 # 
           Fragment.init2(self)
           self.Wakespeed = 15.0 # how fast the Wake leaves the Bird
           self.Wakearc = .9 # 0 = thin Wake stream, 1 = 180 Degrees
           arc = self.Wakespeed * self.Wakearc

           self.dx = dx * self.Wakespeed + random.random()*2*arc - arc
           self.dy = dy * self.Wakespeed + random.random()*2*arc - arc          
            

            

    #------------- end of classes -----------------
    # ----------------- background artwork ------------- 
    picture = pygame.image.load('backgroundslipcopy.png')
    #fore = pygame.image.load('land.png')

    background = pygame.transform.scale(picture, (screen.get_width(), screen.get_height()))
    #foreground = pygame.transform.scale(fore, (screen.get_width(), screen.get_height()))



    background = background.convert()  # jpg can not have transparency
    screen.blit(background, (0,0))     # blit background on screen (overwriting all)
    #-----------------define sprite groups------------------------
    playergroup = pygame.sprite.Group() 
    monstergroup = pygame.sprite.Group()
    bulletgroup = pygame.sprite.Group()
    fragmentgroup = pygame.sprite.Group()
    rocketgroup = pygame.sprite.Group()
    gravitygroup = pygame.sprite.Group()
    projectilegroup = pygame.sprite.Group()
    # only the allgroup draws the sprite, so i use LayeredUpdates() instead Group()
    allgroup = pygame.sprite.LayeredUpdates() # more sophisticated, can draw sprites in layers 

    #-------------loading files from data subdirectory -------------------------------
    try:
        Player.image.append(pygame.image.load(os.path.join(folder,"boater.png")).convert_alpha())   #0
        #Player.image.append(pygame.image.load(os.path.join(folder,"boat.png")).convert_alpha())  #1

        # ------- load sound -------

        #impactsound = pygame.mixer.Sound(os.path.join(folder,'explode.ogg'))
    except:
        raise UserWarning, "Sadly i could not loading all graphic or sound files from %s" % folder
    
    # ------------- before the main loop ----------------------
    #screentext1 = Text("first line", (255,0,255),(0,0))
    #screentext2 = Text("second line",(0,0,0),(0,25))
    #screentext3 = Text("third line", (255,0,0),(0,50))
    #screentext4 = Text("fourth line", (0,0,255),(0,75))
    
    clock = pygame.time.Clock()        # create pygame clock object 
    mainloop = True                    # if False, game ends
    FPS = 60                           # desired max. framerate in frames per second. 
    player1 = Player() # game object number 0
    overtime = 15 # time in seconds to admire the explosion of player before the game ends
    gameOver = False # if True, game still continues until overtime runs out
    gametime = 360 # how long to play (seconds)
    playtime = 0  # how long the game was played
    gravity = False # gravity can be toggled
    screentext = Text()
    crash = False
    
        
    while mainloop:
        milliseconds = clock.tick(FPS)  # milliseconds passed since last frame
        seconds = milliseconds / 1000.0 # seconds passed since last frame
        playtime += seconds # keep track of playtime
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)# pygame window closed by user
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    replay = False
                    sys.exit(0) # user pressed ESC
                if event.key == pygame.K_RETURN:
                    replay = True
                    mainloop = False # user pressed Return
                elif event.key == pygame.K_g:
                    gravity = not gravity # toggle gravity
                elif event.key == pygame.K_o:
                    if gameOver:
                        overtime += 10 # more overtime to watch monsters fight each other
        #---- new Monster ?
        #if random.randint(1,1000) == 1:
        #    Monster()
        pygame.display.set_caption("Boatlaunch. FPS: %.2f"   % clock.get_fps())

            
        for player in playergroup:  # test if a player crash into enemy bullet ... vamipr health stealing effect !
            crashgroup = pygame.sprite.spritecollide(player, bulletgroup, False, pygame.sprite.collide_mask)
            # player vs player
            crashgroup = pygame.sprite.spritecollide(player, playergroup, False, pygame.sprite.collide_circle)
            for crashplayer in crashgroup:
                if player.number > crashplayer.number:
                    elastic_collision(crashplayer, player) # impact on player
                    # player.hitpoints -= crashplayer.damage
                # no damage ?
        
            # test if player crash into enemy rocket
            crashgroup = pygame.sprite.spritecollide(player, rocketgroup, False, pygame.sprite.collide_mask)
            for rocket in crashgroup:
                #if projectile.physicnumber > crashbody.physicnumber: #avoid checking twice
                if rocket.boss.playernumber != player.playernumber: # avoid friendly fire
                   impactsound.play()
                   player.hitpoints -= rocket.damage
                   rocket.boss.rockets_hit += 1
                   Wound(rocket.pos[:])
                   elastic_collision(rocket, player)
                   rocket.kill()
            
        if gravity: # ---- gravity check ---
            for thing in gravitygroup:  # gravity suck down bullets, players, monsters
                thing.dy += 2.81 # pixel per second square earth: 9.81 m/s
        # ------game Over ? -------------

        if GameObject.crashed:
            if GameObject.landed:
                screentext.newmsg("You got the boat on the trailer!  Press Esc to quit or return to play again", (255,0,0))
            else:
                screentext.newmsg("You crashed...  Press Esc to quit or return to play again", (255,0,0))   
            crash = True




        #if  (playtime > gametime) and not gameOver:
        #    gameOver = True # do those things once when the game ends



        # ----------- clear, draw , update, flip -----------------  
        screen.blit(background, (0, 0))
        screen.blit(write("current = " + str(Player.current), (200,200,200)),(0,0))
        screen.blit(write("Steering: W,A,S,D     Current: O,P", (200,200,200)),(500,0))
        
        allgroup.clear(screen, background)
        allgroup.update(seconds)
        allgroup.draw(screen)
        pygame.display.flip()
     

if __name__ == "__main__":
    while True:
        game()

