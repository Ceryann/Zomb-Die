import pygame
import sys
import random

WIDTH = 1024
HEIGHT = 576
FPS = 60

class Character:
    def __init__(self, x, y):
        self.vel_y = 0
        self.vel_x = 0
        self.is_active = True 

    def apply_movement(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

class Bullet(Character): 
    def __init__(self, x, y, vel_x, vel_y):
        super().__init__(x, y) 
        self.image = pygame.Surface((15, 8) if vel_y == 0 else (8, 15))
        self.image.fill((255, 255, 0)) # Warna kuning
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_x = vel_x
        self.vel_y = vel_y

    def update(self):
        self.apply_movement()
        if self.rect.right < -100 or self.rect.left > WIDTH + 100 or self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.is_active = False

class Zombie(Character):
    def __init__(self, x, y, player, score): 
        super().__init__(x, y)
        self.player = player 
        
        # Load gambar zombie
        img = pygame.image.load("zombie.png").convert_alpha()
        self.original_image = pygame.transform.scale(img, (60, 75))
            
        self.image = self.original_image
        self.rect = self.image.get_rect(topleft=(x, y))
        
        speed_boost = score / 40
        self.speed = random.uniform(1.5 + speed_boost, 3.5 + speed_boost) 
        self.gravity = 100

    def update(self):
        # Ngejar player
        if self.rect.x < self.player.rect.x:
            self.vel_x = self.speed  
            self.image = self.original_image
        elif self.rect.x > self.player.rect.x:
            self.vel_x = -self.speed 
            self.image = pygame.transform.flip(self.original_image, True, False)
        else:
            self.vel_x = 0

        self.vel_y += self.gravity
        self.apply_movement()
        
        if self.rect.bottom >= 410: 
            self.rect.bottom = 410
            self.vel_y = 0

class Player(Character):
    def __init__(self, x, y, bullets, suara_tembak): 
        super().__init__(x, y)
        self.bullets = bullets
        self.suara_tembak = suara_tembak 
        
        self.speed = 6
        self.jump_power = -16
        self.gravity = 0.8
        self.on_ground = False
        self.hadap_kanan = True
        self.cd_tembak = 0 # cooldown tembak
        
        self.state = 'leonberdiri'
        self.frame_idx = 0
        self.animasi_speed = 0.15
        
        # Setup animasi
        self.animasi = {'leonberdiri': [], 'run': [], 'tembak_samping': [], 'tembak_bawah': []}
        self.load_animasi()
        
        self.image = self.animasi[self.state][self.frame_idx]
        self.rect = self.image.get_rect(topleft=(x, y))

    def _load_img(self, filename, size):
        img = pygame.image.load(filename).convert_alpha()
        return pygame.transform.scale(img, size)

    def load_animasi(self):
        ukuran = (80, 100)
        self.animasi['leonberdiri'].append(self._load_img("leonberdiri.png", ukuran))
        
        animasiasi_lari = ["leon1.png", "leon2.png", "leon3.png", "leon4.png", "leon5.png", "leon6.png", "leon7.png"]
        for frame in animasiasi_lari:
            self.animasi['run'].append(self._load_img(frame, ukuran))
            
        self.animasi['tembak_samping'].append(self._load_img("tembak_samping.png", ukuran))
        self.animasi['tembak_bawah'].append(self._load_img("tembak_bawah.png", ukuran))

    def move(self, keys):
        self.vel_x = 0
        self.state = 'leonberdiri'
        
        if keys[pygame.K_d]:
            self.vel_x = self.speed
            self.hadap_kanan = True
            self.state = 'run'
        elif keys[pygame.K_a]:
            self.vel_x = -self.speed
            self.hadap_kanan = False
            self.state = 'run'
            
        if (keys[pygame.K_w]) and self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False

        if self.cd_tembak > 0:
            self.cd_tembak -= 1 

        # Logika Nembak
        if keys[pygame.K_RIGHT]:
            self.hadap_kanan = True
            self.state = 'tembak_samping'
            if self.cd_tembak == 0:
                if self.suara_tembak: self.suara_tembak.play() 
                self.shoot(20, 0)
                
        elif keys[pygame.K_LEFT]:
            self.hadap_kanan = False
            self.state = 'tembak_samping'
            if self.cd_tembak == 0:
                if self.suara_tembak: self.suara_tembak.play() 
                self.shoot(-20, 0)
                
        elif keys[pygame.K_DOWN]:
            self.state = 'tembak_bawah'
            if self.cd_tembak == 0:
                if self.suara_tembak: self.suara_tembak.play() 
                self.shoot(0, 20) 

    def shoot(self, vel_x, vel_y):
        b = Bullet(self.rect.centerx, self.rect.centery, vel_x, vel_y)
        self.bullets.append(b)
        self.cd_tembak = 15 # Set ulang cooldown

    def update_animasi(self):
        if len(self.animasi[self.state]) > 1:
            self.frame_idx += self.animasi_speed
            if self.frame_idx >= len(self.animasi[self.state]):
                self.frame_idx = 0
        else:
            self.frame_idx = 0
            
        cur_img = self.animasi[self.state][int(self.frame_idx)]
        # Balik gambar kalau lagi hadap kiri
        self.image = pygame.transform.flip(cur_img, True, False) if not self.hadap_kanan else cur_img

    def update(self):
        self.update_animasi()
        self.vel_y += self.gravity
        self.apply_movement()

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init() 
        pygame.mixer.set_num_channels(16) 
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Zomb Die")
        self.clock = pygame.time.Clock()
        
        pygame.mixer.music.load("soundtrack.mp3")
        pygame.mixer.music.set_volume(0.4) 
        pygame.mixer.music.play(-1) 

        self.suara_tembak = pygame.mixer.Sound("tembak.mp3")
        self.suara_tembak.set_volume(0.6)
            
        self.suara_zombie = pygame.mixer.Sound("zombie.mp3")
        self.suara_zombie.set_volume(0.8)

        self.bg = pygame.image.load("map.jpg").convert()
        self.bg = pygame.transform.scale(self.bg, (WIDTH, HEIGHT))

        self.bullets = []
        self.zombies = []
        
        self.player = Player(150, 300, self.bullets, self.suara_tembak)
        
        self.cam_x = 0
        self.lantai_y = 410
        self.score = 0
        
        self.high_score = self.cek_highscore()
        self.is_game_over = False
        self.hs_saved = False 
        self.timer_zombie = 0

    def cek_highscore(self):
        try:
            with open("highscore.txt", "r") as file:
                return int(file.read())
        except:
            return 0 

    def simpan_highscore(self):
        with open("highscore.txt", "w") as file:
            file.write(str(self.high_score))
            print("Highscore saved!")

    def set_kamera(self):
        # Bikin kamera ngikutin player
        batas_kanan = WIDTH * 0.6
        if self.player.rect.right > batas_kanan:
            geser = self.player.rect.right - batas_kanan
            self.player.rect.right = batas_kanan
            self.cam_x += geser

    def spawn_zombies(self):
        self.timer_zombie += 1
        delay_spawn = max(30, 100 - (self.score // 10) * 2) 
        
        if self.timer_zombie >= delay_spawn:
            self.timer_zombie = 0
            # Munculin zombie random dari kiri atau kanan layar
            arah = random.choice(["kiri", "kanan"])
            x_pos = -100 if arah == "kiri" else WIDTH + 100
            
            z = Zombie(x_pos, 200, self.player, self.score)
            self.zombies.append(z) 

    def cek_tabrakan(self):
        # Cek player kena lantai
        if self.player.rect.bottom >= self.lantai_y:
            self.player.rect.bottom = self.lantai_y
            self.player.vel_y = 0
            self.player.on_ground = True
            
            #batas kiri
            if self.player.rect.left < 0:
               self.player.rect.left = 0
               
        # Cek peluru kena zombie
        for b in self.bullets:
            for z in self.zombies:
                if b.rect.colliderect(z.rect):
                    b.is_active = False   
                    z.is_active = False   
                    if self.suara_zombie:
                        self.suara_zombie.play() 
                    break 

        # Cek player dimakan zombie :(
        for z in self.zombies:
            if self.player.rect.colliderect(z.rect):
                self.is_game_over = True

    def gambar_bg(self):
        rel_x = self.cam_x % WIDTH
        self.screen.blit(self.bg, (-rel_x, 0))
        if rel_x > 0:
            self.screen.blit(self.bg, (WIDTH - rel_x, 0))

    def run(self):
        font_biasa = pygame.font.SysFont("Unesa", 24, bold=True)
        font_mati = pygame.font.SysFont("Chiller", 80)
        
        game_berjalan = True 
        
        while game_berjalan:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.simpan_highscore() 
                    game_berjalan = False 
            
            # Hitung skor berdasarkan jarak jalan
            self.score = int(self.cam_x // 10)
            if self.score > self.high_score:
                self.high_score = self.score

            tombol = pygame.key.get_pressed()

            if not self.is_game_over:
                self.player.move(tombol) 
                self.spawn_zombies() 
                
                self.player.update()
                for b in self.bullets: b.update()
                for z in self.zombies: z.update()
                
                self.cek_tabrakan()
                
                self.bullets[:] = [b for b in self.bullets if b.is_active]
                self.zombies[:] = [z for z in self.zombies if z.is_active]
                
                self.set_kamera()
            else:
                if not self.hs_saved:
                    self.simpan_highscore()
                    self.hs_saved = True
                    pygame.mixer.music.stop() 

            # Render semuanya ke layar
            self.gambar_bg()
            self.screen.blit(self.player.image, self.player.rect)
            
            for b in self.bullets:
                self.screen.blit(b.image, b.rect)
                
            for z in self.zombies:
                self.screen.blit(z.image, z.rect)
            
            # UI Teks
            teks_skor = font_biasa.render(f"Score: {self.score}", True, (255, 50, 50))
            self.screen.blit(teks_skor, (20, 20))
            
            teks_hs = font_biasa.render(f"High Score: {self.high_score}", True, (255, 215, 0))
            self.screen.blit(teks_hs, (20, 55)) 
            
            if self.is_game_over:
                teks_go = font_mati.render("GAME OVER", True, (255, 0, 0))
                posisi_go = teks_go.get_rect(center=(WIDTH//2, HEIGHT//2))
                self.screen.blit(teks_go, posisi_go)
            
            pygame.display.update()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

game = Game()
game.run()