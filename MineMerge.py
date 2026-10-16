import pygame, random, sys, math, os

# ---------- Константы ----------
SCREEN_W, SCREEN_H = 800, 600
BLOCK_SIZE = 32
WORLD_W, WORLD_H = 64, 32

# Цвета блоков
BLOCK_COLORS = {
    0: (0,0,0), 1: (0,180,0), 2: (139,90,43), 3: (100,100,100),
    4: (200,120,50), 5: (50,50,180), 6: (0,100,0), 7: (200,200,0),
    8: (0,200,200), 9: (194,178,128), 10: (139,0,0), 11: (128,0,128)
}
MERGE_COLORS = {i: BLOCK_COLORS[i] for i in range(1,12)}
MERGE_COLORS.update({1:(0,150,0),2:(100,100,100),3:(180,120,50),4:(50,50,180),
                     5:(200,50,200),6:(200,200,0),7:(0,200,200),8:(255,100,100)})

# Рецепты (расширяются при открытии биомов)
BASE_RECIPES = {(1,1):2,(2,2):3,(3,3):4,(4,4):5,(5,5):6,(1,3):7,(2,4):8,(3,5):1}
DESERT_RECIPES = {(9,9):3,(9,3):7,(9,4):10}
HELL_RECIPES = {(10,10):5,(10,4):11,(10,5):8}
END_RECIPES = {(11,11):5,(11,4):6,(11,5):2}
current_recipes = dict(BASE_RECIPES)

# Поле слияния
GRID_COLS, GRID_ROWS = 5, 5
CELL_SIZE = 48
GRID_OFFSET_X = 50
GRID_OFFSET_Y = SCREEN_H - 7*CELL_SIZE - 20
GENERATOR_COL, GENERATOR_ROW = GRID_COLS//2, 0  # ячейка крафтового кольца

# Алтарь и зона базы
ALTAR_X, ALTAR_Y = WORLD_W//2, 20
ZONE_SIZE = 7
ZONE_LEFT = ALTAR_X - ZONE_SIZE//2
ZONE_RIGHT = ALTAR_X + ZONE_SIZE//2
ZONE_TOP = ALTAR_Y - ZONE_SIZE//2
ZONE_BOTTOM = ALTAR_Y + ZONE_SIZE//2

# ---------- Инициализация Pygame ----------
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()
font_small = pygame.font.Font(None, 20)
font_big = pygame.font.Font(None, 24)

# ---------- Глобальные переменные прогрессии ----------
biome_level = 0  # 0-лес,1-пустыня,2-ад,3-край
experience = 0
exp_to_next = {0:5, 1:15, 2:25, 3:99999}
biome_names = ["Лес","Пустыня","Ад","Край"]

# ---------- Генерация мира ----------
def generate_world(biome=0):
    world = [[0]*WORLD_W for _ in range(WORLD_H)]
    for x in range(WORLD_W):
        if biome == 0:  # лес
            h = 15+random.randint(-3,3)
            for y in range(WORLD_H):
                if y < h-2: world[y][x]=0
                elif y==h-2: world[y][x]=1 if random.random()>0.3 else 6
                elif y==h-1: world[y][x]=2
                elif y<h+5: world[y][x]=3
                else: world[y][x]=4 if random.random()<0.02 else 3
        elif biome == 1:  # пустыня
            h = 12+random.randint(-2,2)
            for y in range(WORLD_H):
                if y<h-1: world[y][x]=0
                elif y<h+6: world[y][x]=9
                else: world[y][x]=4 if random.random()<0.03 else 9
        elif biome == 2:  # ад
            h = 18+random.randint(-2,2)
            for y in range(WORLD_H):
                if y<h-3: world[y][x]=0
                elif y<h: world[y][x]=10
                else: world[y][x]=4 if random.random()<0.01 else 10
        else:  # край
            h = 10+random.randint(-2,2)
            for y in range(WORLD_H):
                if y<h-1: world[y][x]=0
                elif y<h+3: world[y][x]=11
                else: world[y][x]=0
    return world

world = generate_world(0)

# ---------- Постройки ----------
buildings = {}
def build_structure(bx,by,lvl,typ):
    if typ=='wall': hp=10*lvl
    elif typ=='turret': hp=5*lvl
    elif typ=='trap': hp=3*lvl
    else: return False
    if (bx,by) in buildings: return False
    buildings[(bx,by)] = {'type':typ,'level':lvl,'hp':hp,'max_hp':hp,'cooldown':0}
    if 0<=bx<WORLD_W and 0<=by<WORLD_H: world[by][bx]=0
    return True

def upgrade_structure(bx,by,new_lvl):
    b = buildings.get((bx,by))
    if not b or new_lvl<=b['level']: return False
    b['level']=new_lvl
    if b['type']=='wall': b['max_hp']=10*new_lvl
    elif b['type']=='turret': b['max_hp']=5*new_lvl
    elif b['type']=='trap': b['max_hp']=3*new_lvl
    b['hp']=b['max_hp']
    return True

# ---------- Персонаж ----------
player_x,player_y = 5,20
player_vy = 0
on_ground = False
speed = 3
selected_build_type = 'wall'

def handle_movement(dt):
    global player_x,player_y,player_vy,on_ground
    keys = pygame.key.get_pressed()
    dx = 0
    if keys[pygame.K_a]: dx=-speed*dt
    if keys[pygame.K_d]: dx=speed*dt
    player_vy += 20*dt
    if keys[pygame.K_w] and on_ground: player_vy=-8
    new_x, new_y = player_x+dx, player_y+player_vy*dt
    def solid(x,y):
        bx,by=int(x),int(y)
        if 0<=bx<WORLD_W and 0<=by<WORLD_H:
            if (bx,by) in buildings: return True
            return world[by][bx]!=0
        return True
    if not solid(new_x,player_y): player_x=new_x
    if not solid(player_x,new_y):
        player_y=new_y
        on_ground=False
    else:
        if player_vy>0: on_ground=True
        player_vy=0
    player_x = max(0,min(WORLD_W-1,player_x))
    player_y = max(0,min(WORLD_H-1,player_y))

def mine_block(grid):
    global world
    bx,by = int(player_x),int(player_y)
    if 0<=bx<WORLD_W and 0<=by<WORLD_H:
        if (bx,by) in buildings: return
        typ = world[by][bx]
        if typ!=0:
            world[by][bx]=0
            for r in range(GRID_ROWS):
                for c in range(GRID_COLS):
                    if grid[r][c]==0:
                        grid[r][c]=typ
                        return

# ---------- Поле слияния (с генератором) ----------
generators = []  # (col,row,Generator)

class Generator:
    def __init__(self,level):
        self.level=level
        self.production_time = max(2,10-level)
        self.remaining = self.production_time
        self.active=True
    def update(self,dt,mf):
        if not self.active: return
        self.remaining-=dt
        if self.remaining<=0:
            if mf.add_item(self.level):
                self.remaining=self.production_time
            else:
                self.remaining=0.1
    def draw(self,surf,x,y):
        pygame.draw.circle(surf,(255,255,0),(x+CELL_SIZE//2,y+CELL_SIZE//2),CELL_SIZE//2-2,3)
        angle = 360*(1-self.remaining/self.production_time)
        if angle>0:
            points=[(x+CELL_SIZE//2,y+CELL_SIZE//2)]
            for a in range(0,int(angle)+1,5):
                rad=math.radians(a-90)
                px=x+CELL_SIZE//2+(CELL_SIZE//2-4)*math.cos(rad)
                py=y+CELL_SIZE//2+(CELL_SIZE//2-4)*math.sin(rad)
                points.append((int(px),int(py)))
            if len(points)>2:
                pygame.draw.polygon(surf,(0,255,0),points)
        text=font_small.render(str(self.level),True,(255,255,255))
        surf.blit(text,(x+CELL_SIZE//2-8,y+CELL_SIZE//2-8))

class MergeField:
    def __init__(self,c,r):
        self.cols=c; self.rows=r
        self.grid=[[0]*c for _ in range(r)]
        self.dragging=False; self.drag_col=self.drag_row=-1; self.drag_level=0
        self.mouse_x=self.mouse_y=0
    def resize(self,nc,nr):
        ng=[[0]*nc for _ in range(nr)]
        for r in range(min(self.rows,nr)):
            for c in range(min(self.cols,nc)):
                ng[r][c]=self.grid[r][c]
        self.grid=ng; self.cols=nc; self.rows=nr
        global GRID_OFFSET_X,GRID_OFFSET_Y,GENERATOR_COL,GENERATOR_ROW
        GRID_OFFSET_X=50; GRID_OFFSET_Y=SCREEN_H-self.rows*CELL_SIZE-20
        GENERATOR_COL=self.cols//2; GENERATOR_ROW=0
    def draw(self,surf):
        pygame.draw.rect(surf,(50,50,50),(GRID_OFFSET_X-5,GRID_OFFSET_Y-5,self.cols*CELL_SIZE+10,self.rows*CELL_SIZE+10))
        for r in range(self.rows):
            for c in range(self.cols):
                x=GRID_OFFSET_X+c*CELL_SIZE; y=GRID_OFFSET_Y+r*CELL_SIZE
                pygame.draw.rect(surf,(80,80,80),(x,y,CELL_SIZE,CELL_SIZE),2)
                lvl=self.grid[r][c]
                if lvl>0:
                    color=MERGE_COLORS.get(lvl,(255,255,255))
                    pygame.draw.rect(surf,color,(x+2,y+2,CELL_SIZE-4,CELL_SIZE-4))
                    text=font_small.render(str(lvl),True,(255,255,255))
                    surf.blit(text,(x+12,y+12))
                for gc,gr,gen in generators:
                    if gc==c and gr==r:
                        gen.draw(surf,x,y); break
        gx=GRID_OFFSET_X+GENERATOR_COL*CELL_SIZE; gy=GRID_OFFSET_Y+GENERATOR_ROW*CELL_SIZE
        pygame.draw.circle(surf,(255,255,0),(gx+CELL_SIZE//2,gy+CELL_SIZE//2),CELL_SIZE//2+2,3)
    def handle_mouse_down(self,pos):
        col=(pos[0]-GRID_OFFSET_X)//CELL_SIZE; row=(pos[1]-GRID_OFFSET_Y)//CELL_SIZE
        if 0<=col<self.cols and 0<=row<self.rows and self.grid[row][col]>0:
            self.dragging=True; self.drag_col=col; self.drag_row=row
            self.drag_level=self.grid[row][col]; self.grid[row][col]=0
    def handle_mouse_up(self,pos):
        global generators
        if not self.dragging: return
        col=(pos[0]-GRID_OFFSET_X)//CELL_SIZE; row=(pos[1]-GRID_OFFSET_Y)//CELL_SIZE
        if 0<=col<self.cols and 0<=row<self.rows:
            target=self.grid[row][col]
            if col==GENERATOR_COL and row==GENERATOR_ROW:
                exist = next((i for i,(gc,gr,_) in enumerate(generators) if gc==col and gr==row), None)
                if exist is not None:
                    gen=generators[exist][2]
                    lvl=gen.level
                    generators.pop(exist)
                    if not self.add_item(lvl):
                        self.grid[row][col]=lvl
                else:
                    if self.drag_level>0:
                        generators.append((col,row,Generator(self.drag_level)))
            else:
                if target==0:
                    self.grid[row][col]=self.drag_level
                else:
                    combo=(min(self.drag_level,target),max(self.drag_level,target))
                    if combo in current_recipes:
                        self.grid[row][col]=current_recipes[combo]
                    elif target==self.drag_level and target<11:
                        self.grid[row][col]=target+1
                    else:
                        self.grid[self.drag_row][self.drag_col]=target
                        self.grid[row][col]=self.drag_level
        else:
            self.grid[self.drag_row][self.drag_col]=self.drag_level
        self.dragging=False
    def handle_mouse_motion(self,pos):
        if self.dragging:
            self.mouse_x,self.mouse_y=pos
    def draw_drag(self,surf):
        if self.dragging:
            color=MERGE_COLORS.get(self.drag_level,(255,255,255))
            x,y=self.mouse_x,self.mouse_y
            pygame.draw.rect(surf,color,(x-CELL_SIZE//2,y-CELL_SIZE//2,CELL_SIZE,CELL_SIZE))
            text=font_small.render(str(self.drag_level),True,(255,255,255))
            surf.blit(text,(x-10,y-10))
    def find_first_empty(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c]==0 and not any(gc==c and gr==r for gc,gr,_ in generators):
                    return (c,r)
        return None
    def add_item(self,lvl):
        pos=self.find_first_empty()
        if pos:
            self.grid[pos[1]][pos[0]]=lvl
            return True
        return False

merge_field = MergeField(5,5)

# ---------- Мобы ----------
class Mob:
    def __init__(self,x,y,typ,diff,biome):
        self.x=x; self.y=y; self.type=typ; self.biome=biome; self.difficulty=diff
        if typ=='zombie': self.max_hp=30*diff; self.speed=0.8; self.damage=10*diff
        elif typ=='creeper': self.max_hp=20*diff; self.speed=1.2; self.damage=30*diff
        elif typ=='skeleton': self.max_hp=15*diff; self.speed=1.0; self.damage=8*diff
        if biome==1: self.speed*=1.2; self.max_hp*=0.8
        elif biome==2: self.max_hp*=1.5; self.damage*=1.3
        elif biome==3: self.speed*=1.1; self.max_hp*=0.9
        self.hp=self.max_hp; self.alive=True; self.attack_cd=0
    def update(self,dt,world,buildings):
        if not self.alive: return
        dx=ALTAR_X-self.x; dy=ALTAR_Y-self.y
        dist=math.hypot(dx,dy)
        if dist>0.5:
            step_x=(dx/dist)*self.speed*dt; step_y=(dy/dist)*self.speed*dt
            nx=self.x+step_x; ny=self.y+step_y
            bx,by=int(nx),int(ny)
            if (bx,by) in buildings:
                b=buildings[(bx,by)]
                if b['type']!='trap':
                    if self.attack_cd<=0:
                        b['hp']-=self.damage*dt
                        self.attack_cd=0.5
                        if b['hp']<=0: del buildings[(bx,by)]
                    self.attack_cd-=dt
                else:
                    self.hp-=20
                    if self.hp<=0: self.alive=False
                    self.x=nx; self.y=ny
            else:
                self.x=nx; self.y=ny
        else:
            pass
    def take_damage(self,amount):
        self.hp-=amount
        if self.hp<=0: self.alive=False; self.on_death()
    def on_death(self):
        global experience
        experience+=1
        if random.random()<0.5:
            lvl=random.randint(1,3)
            merge_field.add_item(lvl)
    def render(self,surf,cam_x,cam_y):
        if not self.alive: return
        sx=self.x*BLOCK_SIZE-cam_x; sy=self.y*BLOCK_SIZE-cam_y
        color={'zombie':(255,0,0),'creeper':(0,255,0),'skeleton':(0,0,255)}.get(self.type,(128,128,128))
        pygame.draw.rect(surf,color,(sx+2,sy+2,BLOCK_SIZE-4,BLOCK_SIZE-4))
        hp_ratio=self.hp/self.max_hp
        pygame.draw.rect(surf,(0,255,0),(sx,sy-4,int(BLOCK_SIZE*hp_ratio),3))
        pygame.draw.rect(surf,(255,0,0),(sx+int(BLOCK_SIZE*hp_ratio),sy-4,int(BLOCK_SIZE*(1-hp_ratio)),3))

mobs=[]
wave_number=0; wave_timer=0; wave_active=False; spawn_timer=0
def start_wave():
    global wave_active,wave_number,spawn_timer
    wave_number+=1; wave_active=True; spawn_timer=0
def update_waves(dt):
    global wave_timer,wave_active,spawn_timer,mobs,experience
    wave_timer+=dt
    if wave_timer>=15: start_wave(); wave_timer=0
    if wave_active:
        spawn_timer+=dt
        to_spawn=int(2+wave_number*1.5)
        if spawn_timer>=3 and len(mobs)<to_spawn:
            side=random.choice(['left','right','top','bottom'])
            if side=='left': sx=ZONE_LEFT-random.randint(2,5); sy=random.randint(ZONE_TOP,ZONE_BOTTOM)
            elif side=='right': sx=ZONE_RIGHT+random.randint(2,5); sy=random.randint(ZONE_TOP,ZONE_BOTTOM)
            elif side=='top': sx=random.randint(ZONE_LEFT,ZONE_RIGHT); sy=ZONE_TOP-random.randint(2,5)
            else: sx=random.randint(ZONE_LEFT,ZONE_RIGHT); sy=ZONE_BOTTOM+random.randint(2,5)
            sx=max(1,min(WORLD_W-1,sx)); sy=max(1,min(WORLD_H-1,sy))
            typ=random.choice(['zombie','creeper','skeleton'])
            mob=Mob(sx,sy,typ,1+wave_number*0.2,biome_level)
            mobs.append(mob); spawn_timer=0
        if len(mobs)>=to_spawn:
            wave_active=False; experience+=5

# ---------- Снаряды турелей ----------
projectiles=[]
class Projectile:
    def __init__(self,x,y,target,damage):
        self.x=x; self.y=y; self.target=target; self.damage=damage; self.speed=5; self.alive=True
    def update(self,dt):
        if not self.alive or not self.target.alive: self.alive=False; return
        dx=self.target.x-self.x; dy=self.target.y-self.y
        dist=math.hypot(dx,dy)
        if dist<0.5: self.target.take_damage(self.damage); self.alive=False
        else: step=self.speed*dt; self.x+=(dx/dist)*step; self.y+=(dy/dist)*step
    def render(self,surf,cam_x,cam_y):
        if not self.alive: return
        sx=self.x*BLOCK_SIZE-cam_x+BLOCK_SIZE//2; sy=self.y*BLOCK_SIZE-cam_y+BLOCK_SIZE//2
        pygame.draw.circle(surf,(255,255,0),(int(sx),int(sy)),4)

def update_turrets(dt):
    global projectiles
    for (bx,by),b in list(buildings.items()):
        if b['type']=='turret' and b['hp']>0:
            b['cooldown']-=dt
            if b['cooldown']<=0:
                closest=None; min_dist=10*BLOCK_SIZE
                for mob in mobs:
                    if mob.alive:
                        d=math.hypot(mob.x-bx,mob.y-by)
                        if d<min_dist: min_dist=d; closest=mob
                if closest:
                    projectiles.append(Projectile(bx,by,closest,15*b['level']))
                    b['cooldown']=1

# ---------- Меню ----------
class MainMenu:
    def __init__(self):
        self.play=pygame.Rect(SCREEN_W//2-100,200,200,50)
        self.sett=pygame.Rect(SCREEN_W//2-100,280,200,50)
        self.quit=pygame.Rect(SCREEN_W//2-100,360,200,50)
    def draw(self,surf):
        surf.fill((50,50,80))
        title=font_big.render("MineMerge",True,(255,215,0))
        surf.blit(title,(SCREEN_W//2-80,100))
        for rect,text in [(self.play,"Играть"),(self.sett,"Настройки"),(self.quit,"Выход")]:
            pygame.draw.rect(surf,(100,100,100),rect,border_radius=5)
            txt=font_big.render(text,True,(255,255,255))
            surf.blit(txt,(rect.x+50,rect.y+10))
    def handle(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN:
            if self.play.collidepoint(event.pos): return 'play'
            if self.sett.collidepoint(event.pos): return 'settings'
            if self.quit.collidepoint(event.pos): return 'quit'
        return None

# ---------- Мобильный контроллер ----------
class MobileController:
    def __init__(self):
        self.joystick_rect=pygame.Rect(30,SCREEN_H-200,150,150)
        self.action_rect=pygame.Rect(SCREEN_W-120,SCREEN_H-120,100,100)
        self.jx=self.jy=0; self.active=False
    def handle_touch(self,event):
        if event.type==pygame.FINGERDOWN:
            x,y=event.x*SCREEN_W,event.y*SCREEN_H
            if self.joystick_rect.collidepoint(x,y): self.active=True; return
            if self.action_rect.collidepoint(x,y): return 'action'
        elif event.type==pygame.FINGERUP:
            self.active=False; self.jx=self.jy=0
        elif event.type==pygame.FINGERMOTION and self.active:
            x,y=event.x*SCREEN_W,event.y*SCREEN_H
            cx,cy=self.joystick_rect.center
            dx,dy=x-cx,y-cy
            max_r=self.joystick_rect.width//2
            dist=math.hypot(dx,dy)
            if dist>max_r: dx=dx*max_r/dist; dy=dy*max_r/dist
            self.jx=dx/max_r; self.jy=dy/max_r
        return None
    def draw(self,surf):
        pygame.draw.circle(surf,(200,200,200),self.joystick_rect.center,70,3)
        pygame.draw.circle(surf,(100,100,100),
                           (self.joystick_rect.centerx+int(self.jx*50),self.joystick_rect.centery+int(self.jy*50)),20)
        pygame.draw.rect(surf,(200,50,50),self.action_rect,border_radius=10)
        text=font_small.render("E",True,(255,255,255))
        surf.blit(text,(self.action_rect.x+40,self.action_rect.y+35))

# ---------- Туториал ----------
tutorial_steps = [
    "Добро пожаловать! WASD – движение, E – добыть блок.",
    "Нажми 1,2,3 для выбора постройки (стена, турель, ловушка).",
    "ПКМ по пустой клетке в зоне базы – построить.",
    "Перетаскивай тайлы на поле слияния (ЛКМ).",
    "Два одинаковых тайла сливаются в уровень выше.",
    "Крафтовое кольцо (жёлтая ячейка) – генератор.",
    "Убивай мобов, получай опыт и открывай новые биомы!"
]
tutorial_step=0; show_tutorial=True

# ---------- Основной цикл ----------
menu = MainMenu()
mobile = MobileController()
show_menu = True
running = True
paused = False
dt = 0.016

while running:
    dt = clock.tick(60)/1000.0
    if show_menu:
        for event in pygame.event.get():
            if event.type==pygame.QUIT: running=False
            act=menu.handle(event)
            if act=='play': show_menu=False
            elif act=='quit': running=False
        menu.draw(screen)pygame.display.flip()
        continue

    # Туториал (первый раз)
    if show_tutorial and tutorial_step<len(tutorial_steps):
        overlay=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        screen.blit(overlay,(0,0))
        text=font_big.render(tutorial_steps[tutorial_step],True,(255,255,255))
        screen.blit(text,(100,200))
        hint=font_small.render("Нажмите любую клавишу / тап",True,(200,200,200))
        screen.blit(hint,(300,400))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type in (pygame.KEYDOWN,pygame.MOUSEBUTTONDOWN,pygame.FINGERDOWN):
                tutorial_step+=1
                if tutorial_step>=len(tutorial_steps): show_tutorial=False
        continue

    # Обработка событий
    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_p: paused=not paused
            if event.key==pygame.K_e: mine_block(merge_field.grid)
            if event.key==pygame.K_r:
                world=generate_world(biome_level)
                buildings.clear(); mobs.clear(); projectiles.clear(); generators.clear()
            if event.key==pygame.K_1: selected_build_type='wall'
            if event.key==pygame.K_2: selected_build_type='turret'
            if event.key==pygame.K_3: selected_build_type='trap'
            if event.key==pygame.K_t:
                for _ in range(3):
                    x=random.randint(ZONE_LEFT-3,ZONE_RIGHT+3)
                    y=random.randint(ZONE_TOP-3,ZONE_BOTTOM+3)
                    mobs.append(Mob(x,y,random.choice(['zombie','creeper','skeleton']),1,biome_level))
        if not paused:
            # Мышь (ПК)
            if event.type==pygame.MOUSEBUTTONDOWN:
                if event.button==1:
                    merge_field.handle_mouse_down(event.pos)
                elif event.button==3:
                    bx=(event.pos[0]+cam_x)//BLOCK_SIZE
                    by=(event.pos[1]+cam_y)//BLOCK_SIZE
                    if (ZONE_LEFT<=bx<=ZONE_RIGHT and ZONE_TOP<=by<=ZONE_BOTTOM and
                        0<=bx<WORLD_W and 0<=by<WORLD_H and (bx,by) not in buildings and world[by][bx]==0):
                        for r in range(merge_field.rows):
                            for c in range(merge_field.cols):
                                if merge_field.grid[r][c]>0:
                                    lvl=merge_field.grid[r][c]
                                    merge_field.grid[r][c]=0
                                    build_structure(bx,by,lvl,selected_build_type)
                                    break
                            else: continue
                            break
                    else:
                        if merge_field.dragging:
                            merge_field.grid[merge_field.drag_row][merge_field.drag_col]=merge_field.drag_level
                            merge_field.dragging=False
            if event.type==pygame.MOUSEBUTTONUP:
                if event.button==1: merge_field.handle_mouse_up(event.pos)
            if event.type==pygame.MOUSEMOTION:
                merge_field.handle_mouse_motion(event.pos)
            # Тач (мобильный)
            if event.type in (pygame.FINGERDOWN,pygame.FINGERUP,pygame.FINGERMOTION):
                act=mobile.handle_touch(event)
                if act=='action': mine_block(merge_field.grid)

    if not paused:
        # Движение (клавиши + джойстик)
        keys=pygame.key.get_pressed()
        dx=0; dy=0
        if keys[pygame.K_a] or mobile.jx<-0.3: dx=-speed*dt
        if keys[pygame.K_d] or mobile.jx>0.3: dx=speed*dt
        if keys[pygame.K_w] or mobile.jy<-0.3: dy=-speed*dt
        if keys[pygame.K_s] or mobile.jy>0.3: dy=speed*dt
        # Движение без гравитации для простоты (можно заменить на handle_movement)
        nx=player_x+dx; ny=player_y+dy
        if 0<=nx<WORLD_W and 0<=ny<WORLD_H and world[int(ny)][int(nx)]==0 and (int(nx),int(ny)) not in buildings:
            player_x=nx; player_y=ny

        update_waves(dt)
        for mob in mobs[:]:
            mob.update(dt,world,buildings)
            if not mob.alive: mobs.remove(mob)
        update_turrets(dt)
        for proj in projectiles[:]:
            proj.update(dt)
            if not proj.alive or not proj.target.alive: projectiles.remove(proj)
        # Обновление генераторов
        for gen in generators[:]:
            gen[2].update(dt,merge_field)
        # Проверка прогрессии
        if biome_level<3 and experience>=exp_to_next[biome_level]:
            biome_level+=1; experience=0
            world=generate_world(biome_level)
            buildings.clear(); mobs.clear(); projectiles.clear(); generators.clear()
            if biome_level==1: current_recipes.update(DESERT_RECIPES)
            elif biome_level==2: current_recipes.update(HELL_RECIPES)
            elif biome_level==3: current_recipes.update(END_RECIPES)
            new_c=min(7,merge_field.cols+1); new_r=min(7,merge_field.rows+1)
            merge_field.resize(new_c,new_r)
            player_x,player_y=5,20

    # Камера
    cam_x=player_x*BLOCK_SIZE-SCREEN_W//2+BLOCK_SIZE//2
    cam_y=player_y*BLOCK_SIZE-(SCREEN_H-merge_field.rows*CELL_SIZE-40)//2+BLOCK_SIZE//2
    cam_x=max(0,min(WORLD_W*BLOCK_SIZE-SCREEN_W,cam_x))
    cam_y=max(0,min(WORLD_H*BLOCK_SIZE-(SCREEN_H-merge_field.rows*CELL_SIZE-40),cam_y))

    # Отрисовка
    screen.fill((135,206,235))
    # Мир
    vl=max(0,int(cam_x//BLOCK_SIZE)); vr=min(WORLD_W,int((cam_x+SCREEN_W)//BLOCK_SIZE)+1)
    vt=max(0,int(cam_y//BLOCK_SIZE)); vb=min(WORLD_H,int((cam_y+SCREEN_H)//BLOCK_SIZE)+1))
    for y in range(vt,vb):
        for x in range(vl,vr):
            b=world[y][x]
            if b:
                sx=x*BLOCK_SIZE-cam_x; sy=y*BLOCK_SIZE-cam_y
                pygame.draw.rect(screen,BLOCK_COLORS.get(b,(255,255,255)),(sx,sy,BLOCK_SIZE,BLOCK_SIZE))
    # Зона базы
    zx=ZONE_LEFT*BLOCK_SIZE-cam_x; zy=ZONE_TOP*BLOCK_SIZE-cam_y
    for i in range(0,ZONE_SIZE*BLOCK_SIZE,8):
        pygame.draw.rect(screen,(255,255,0),(zx+i,zy,4,BLOCK_SIZE//2),1)
        pygame.draw.rect(screen,(255,255,0),(zx+i,zy+ZONE_SIZE*BLOCK_SIZE-BLOCK_SIZE//2,4,BLOCK_SIZE//2),1)
    for i in range(0,ZONE_SIZE*BLOCK_SIZE,8):
        pygame.draw.rect(screen,(255,255,0),(zx,zy+i,BLOCK_SIZE//2,4),1)
        pygame.draw.rect(screen,(255,255,0),(zx+ZONE_SIZE*BLOCK_SIZE-BLOCK_SIZE//2,zy+i,BLOCK_SIZE//2,4),1)
    # Алтарь
    ax=ALTAR_X*BLOCK_SIZE-cam_x; ay=ALTAR_Y*BLOCK_SIZE-cam_y
    pygame.draw.rect(screen,(255,215,0),(ax,ay,BLOCK_SIZE,BLOCK_SIZE))
    txt=font_big.render("C",True,(0,0,0))
    screen.blit(txt,(ax+4,ay+4))
    # Постройки
    for (bx,by),b in buildings.items():
        sx=bx*BLOCK_SIZE-cam_x; sy=by*BLOCK_SIZE-cam_y
        col={'wall':(150,80,30),'urret':(200,0,0),'rap':(100,0,100)}.et(b['type'],(255,255,255))
        pygame.draw.rect(screen,col,(sx+2,sy+2,BLOCK_SIZE-4,BLOCK_SIZE-4))
        pygame.draw.rect(screen,(0,0,0),(sx,sy,BLOCK_SIZE,BLOCK_SIZE),2)
        lvl_t=font_small.render(str(b['level']),True,(255,255,255))
        screen.blit(lvl_t,(sx+4,sy+4))
        hp_r=b['hp']/['max_hp']
        if hp_r<1:
            pygame.draw.rect(screen,(255,0,0),(sx,sy-4,BLOCK_SIZE,3))
            pygame.draw.rect(screen,(0,255,0),(sx,sy-4,int(BLOCK_SIZE*hp_r),3))
    # Мобы
    for mob in mobs: mob.render(screen,cam_x,cam_y)
    # Сняряды
    for proj in projectiles: proj.render(screen,cam_x,cam_y)
    # Персонаж
    px=player_x*BLOCK_SIZE-cam_x; py=player_y*BLOCK_SIZE-cam_y
    pygame.draw.rect(screen,(0,0,255),(px,py,BLOCK_SIZE,BLOCK_SIZE))
    # Поле слияния
    merge_field.draw(screen)
    merge_field.draw_drag(screen)
    # Мобильное управление
    mobile.draw(screen)
    # UI
    info=f"Волна:{wave_number} Опыт:{experience}/{exp_to_next[biome_level]} Биом:{biome_names[biome_level]}"
    screen.blit(font_small.render(info,True,(255,255,255)),(10,10))
    screen.blit(font_small.render("WASD-движение E-добыть 1,2,3-постройки P-пауза",True,(200,200,200)),(10,30))
    if paused:
        overlay=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)overlay.fill((0,0,0,128))
        screen.blit(overlay,(0,0))
        screen.blit(font_big.render("Пауза",True,(255,255,255)),(SCREEN_W//2-50,SCREEN_H//2))
    pygame.display.flip()

pygame.quit()
sys.exit()