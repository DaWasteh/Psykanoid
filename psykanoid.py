import pygame
import random
import math
import sys

# ============================================================================
# KONSTANTEN & INITIALISIERUNG
# ============================================================================
pygame.init()

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Spielmodus (Module-Level für Paddle-Klassen Zugriff)
GAME_MODE = "2PLAYER"

# Farben (2000er Neon-Stil)
BG_COLOR = (10, 10, 20)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
COLOR_P1 = (0, 255, 240)      # Neon-Cyan
COLOR_P2 = (255, 60, 120)     # Neon-Rosa
COLOR_P1_DARK = (0, 180, 170)  # Dunkleres Cyan für Schatten
COLOR_P2_DARK = (180, 30, 80)  # Dunkleres Rosa für Schatten

# Steinfarben (2000er Neon-Palette)
BRICK_COLORS = [
    (255, 50, 80),     # Neon-Rot
    (255, 120, 40),    # Neon-Orange
    (255, 220, 0),     # Neon-Gelb
    (80, 255, 120),    # Neon-Grün
    (0, 255, 200),     # Neon-Türkis
    (80, 120, 255),    # Neon-Blau
    (180, 60, 255),    # Neon-Lila
    (255, 80, 200)     # Neon-Magenta
]
COLOR_BRICK_DAMAGED = (200, 120, 80) # Orange-grau nach dem ersten Treffer

# Partikel-Klasse für Explosions-Effekte
class Particle:
    """Ein einzelnes Partikel für Explosions-Effekte."""
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.dx = random.uniform(-3, 3)
        self.dy = random.uniform(-3, 3)
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.05)
        self.size = random.randint(2, 5)
        self.color = color
        
    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.1  # Schwerkraft
        self.life -= self.decay
        
    def draw(self, screen):
        if self.life <= 0:
            return
        size = max(1, int(self.size * self.life))
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(surf, (*self.color[:3], int(255 * self.life)), (0, 0, size, size))
        screen.blit(surf, (int(self.x - size/2), int(self.y - size/2)))


def create_background_surface():
    """Erstellt einen radialen Gradient-Hintergrund für den Spielfeld."""
    bg_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg_surf.fill(BG_COLOR)
    # Subtiler radialer Gradient von der Mitte
    center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    max_radius = max(SCREEN_WIDTH, SCREEN_HEIGHT) // 2
    for radius in range(max_radius, 0, -1):
        alpha = int(40 * (1 - radius / max_radius))
        color = (20, 20, 60, alpha)  # Bläulicher Schimmer in der Mitte
        rect = pygame.Rect(center_x - radius, center_y - radius, radius * 2, radius * 2)
        # Nur den Ring zeichnen (effizienter)
        if radius % 5 == 0:  # Alle 5 Pixel einen Ring
            pygame.draw.ellipse(bg_surf, (*color[:3], alpha), rect, 1)
    return bg_surf

# Spiel-Dimensionen
PADDLE_WIDTH = 120
PADDLE_HEIGHT = 15
PADDLE_SPEED = 8
PADDLE_CORNER_RADIUS = 8  # Abgerundete Ecken

BALL_RADIUS = 8
BASE_BALL_SPEED = 7

GRID_ROWS = 6
GRID_COLS = 10
BRICK_WIDTH = 80
BRICK_HEIGHT = 25
BRICK_PADDING = 8
BRICK_OFFSET_TOP = 70
BRICK_BORDER_RADIUS = 4  # Abgerundete Steine

# Leben
MAX_LIVES = 3

# ============================================================================
# SOUND MANAGER
# ============================================================================
class SoundManager:
    """
    Verwaltet alle Sounds im Spiel.
    
    WICHTIGER HINWEIS FÜR .WAV DATEIEN:
    Um eigene Sounds zu nutzen, kommentiere die Synth-Generierung aus und 
    nutze pygame.mixer.Sound() wie hier gezeigt:
    
    self.sounds['wall_hit'] = pygame.mixer.Sound('sounds/wall_hit.wav')
    self.sounds['brick_hit'] = pygame.mixer.Sound('sounds/brick_hit.wav')
    self.sounds['paddle_hit'] = pygame.mixer.Sound('sounds/paddle_hit.wav')
    self.sounds['game_over'] = pygame.mixer.Sound('sounds/game_over.wav')
    """

    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        self._load_synth_sounds()

    def _load_synth_sounds(self):
        """Generiert einfache synthetische Beeps ohne externe Dateien."""
        try:
            import numpy as np
            sample_rate = 44100
            
            def make_beep(freq, duration, vol=0.1):
                t = np.linspace(0, duration, int(sample_rate * duration), False)
                wave = np.sin(freq * t * 2 * np.pi)
                audio = np.zeros((len(t), 2), dtype=np.int16)
                max_amp = 32767 * vol
                audio[:, 0] = wave * max_amp
                audio[:, 1] = wave * max_amp
                return pygame.sndarray.make_sound(audio)

            self.sounds['paddle_hit'] = make_beep(440, 0.1)
            self.sounds['brick_hit'] = make_beep(880, 0.1)
            self.sounds['wall_hit'] = make_beep(220, 0.1)
            self.sounds['game_over'] = make_beep(110, 0.5, 0.3)
            self.sounds['life_lost'] = make_beep(150, 0.3, 0.2)
        except ImportError:
            print("Info: NumPy nicht gefunden. Synthetische Sounds werden deaktiviert.")
            self.sounds = {} # Bleibt stumm, Spiel crasht aber nicht

    def play(self, name):
        if name in self.sounds and self.sounds[name]:
            self.sounds[name].play()


# ============================================================================
# SPIEL-OBJEKTE
# ============================================================================
class Paddle:
    def __init__(self, x, color, player_num):
        self.rect = pygame.Rect(x, SCREEN_HEIGHT - 50, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.color = color
        self.player_num = player_num
        self.speed = PADDLE_SPEED

    def move(self, keys):
        if self.player_num == 1:
            # Singleplayer oder Spieler 1 in 2-Player Modus
            if keys[pygame.K_a] and self.rect.left > 0:
                self.rect.x -= self.speed
            if keys[pygame.K_d] and self.rect.right < SCREEN_WIDTH:
                self.rect.x += self.speed
        else:
            # Nur Spieler 2 in 2-Player Modus
            if GAME_MODE == "2PLAYER":
                if keys[pygame.K_LEFT] and self.rect.left > 0:
                    self.rect.x -= self.speed
                if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
                    self.rect.x += self.speed

    def draw(self, screen):
        # Mehrschichtiger Glow-Effekt (wie 2000er Neon)
        for i in range(3, 0, -1):
            glow_size = self.rect.width + i * 8
            glow_height = self.rect.height + i * 8
            alpha = max(5, 30 - i * 10)
            glow_surf = pygame.Surface((glow_size, glow_height), pygame.SRCALPHA)
            glow_rect = pygame.Rect(0, 0, glow_size, glow_height)
            pygame.draw.rect(glow_surf, (*self.color[:3], alpha), glow_rect,
                           border_radius=PADDLE_CORNER_RADIUS + i * 2)
            screen.blit(glow_surf, (self.rect.x - i * 4, self.rect.y - i * 4))
        
        # Hauptpaddle mit abgerundeten Ecken und Farbverlauf-Effekt
        pygame.draw.rect(screen, self.color, self.rect, border_radius=PADDLE_CORNER_RADIUS)
        
        # Hellerer Strich oben für 3D-Effekt
        highlight = pygame.Surface((self.rect.width - 10, 5), pygame.SRCALPHA)
        highlight_color = (*self.color[:3], 150)
        pygame.draw.rect(highlight, highlight_color, (0, 0, self.rect.width - 10, 5), border_radius=3)
        screen.blit(highlight, (self.rect.x + 5, self.rect.y + 2))
        
        # Unten dunklerer Strich für Schatten-Effekt
        shadow = pygame.Surface((self.rect.width - 10, 3), pygame.SRCALPHA)
        shadow_color = (*self.color[:3], 80)
        pygame.draw.rect(shadow, shadow_color, (0, 0, self.rect.width - 10, 3), border_radius=2)
        screen.blit(shadow, (self.rect.x + 5, self.rect.y + self.rect.height - 5))
        
        # Weißer Rand
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=PADDLE_CORNER_RADIUS)


class Ball:
    def __init__(self, x, y, color, player_num):
        self.color = color
        self.player_num = player_num
        self.radius = BALL_RADIUS
        self.trail = []  # Trail für Schweifeffekt
        self.max_trail = 8
        self.reset(x, y)

    def reset(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.trail = []
        self.launched = False  # Ball klebt am Paddle bis zur Starttaste
        
        # Zufälliger Startwinkel (leicht nach oben) - wird beim Start verwendet
        self._launch_angle = random.uniform(math.pi/4, 3*math.pi/4)
        if self.player_num == 2:
            self._launch_angle += math.pi # P2 ball startet in eine andere Richtung
        
        # Ball startet mit Geschwindigkeit 0 (klebt am Paddle)
        self.dx = 0
        self.dy = 0

    def launch(self):
        """Startet den Ball mit zufälligem Winkel (wenn er noch am Paddle klebt)."""
        if not self.launched:
            self.launched = True
            self.dx = BASE_BALL_SPEED * math.cos(self._launch_angle)
            self.dy = -BASE_BALL_SPEED * abs(math.sin(self._launch_angle))

    def update(self, paddle=None):
        # Wenn Ball noch nicht gestartet wurde, klebt er am Paddle
        if not self.launched and paddle:
            self.x = paddle.rect.centerx
            self.y = paddle.rect.top - self.radius
            return
        
        # Alte Position für Trail speichern
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)
        
        self.x += self.dx
        self.y += self.dy

    def get_rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def draw(self, screen):
        # Trail-Schweifeffekt (wie 2000er Arcade)
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(80 * (i / self.max_trail))
            size = int(self.radius * 0.6 * (i / self.max_trail))
            if size > 0:
                trail_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, (*self.color[:3], alpha),
                                 (size, size), size)
                screen.blit(trail_surf, (int(tx - size), int(ty - size)))
        
        # Mehrschichtiger Glow-Effekt
        for i in range(4, 0, -1):
            glow_radius = self.radius + i * 4
            alpha = max(5, 50 - i * 12)
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color[:3], alpha),
                             (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surf, (int(self.x - glow_radius), int(self.y - glow_radius)))
        
        # Hauptball
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        
        # Lichtpunkt (3D-Effekt)
        light_offset = self.radius // 3
        pygame.draw.circle(screen, WHITE, (int(self.x - light_offset), int(self.y - light_offset)), 2)


class Brick:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
        self.base_color = color
        
        # 30% Chance für einen 2-Treffer-Stein
        self.max_hits = 2 if random.random() < 0.3 else 1
        self.hits = 0

    def hit(self):
        self.hits += 1
        return self.hits >= self.max_hits

    def draw(self, screen):
        # Farbwechsel nach dem ersten Treffer
        current_color = COLOR_BRICK_DAMAGED if self.hits > 0 and self.max_hits == 2 else self.base_color
        
        # Schatten (versetzt)
        shadow_rect = self.rect.move(3, 3)
        pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=BRICK_BORDER_RADIUS + 1)
        
        # Hauptstein mit abgerundeten Ecken und Farbverlauf-Effekt
        pygame.draw.rect(screen, current_color, self.rect, border_radius=BRICK_BORDER_RADIUS)
        
        # Oberseite heller (3D-Effekt)
        highlight = pygame.Surface((self.rect.width - 6, 4), pygame.SRCALPHA)
        highlight_color = (*current_color[:3], 120)
        pygame.draw.rect(highlight, highlight_color, (0, 0, self.rect.width - 6, 4), border_radius=3)
        screen.blit(highlight, (self.rect.x + 3, self.rect.y + 2))
        
        # Unterseite dunkler
        shadow = pygame.Surface((self.rect.width - 6, 2), pygame.SRCALPHA)
        shadow_color = (*current_color[:3], 60)
        pygame.draw.rect(shadow, shadow_color, (0, 0, self.rect.width - 6, 2), border_radius=2)
        screen.blit(shadow, (self.rect.x + 3, self.rect.y + self.rect.height - 4))
        
        # Linker Rand leicht heller
        left_highlight = pygame.Surface((2, self.rect.height - 4), pygame.SRCALPHA)
        left_color = (*current_color[:3], 60)
        pygame.draw.rect(left_highlight, left_color, (0, 0, 2, self.rect.height - 4), border_radius=1)
        screen.blit(left_highlight, (self.rect.x + 1, self.rect.y + 2))
        
        # Weißer Rand
        pygame.draw.rect(screen, WHITE, self.rect, 1, border_radius=BRICK_BORDER_RADIUS)
        
        # 2-Treffer-Anzeige (kleiner Punkt)
        if self.max_hits == 2 and self.hits == 0:
            pygame.draw.circle(screen, WHITE, (self.rect.centerx, self.rect.centery), 3)


# ============================================================================
# HAUPTSPIEL-KLASSE
# ============================================================================
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Psykanoid - Breakout")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 72)
        
        self.sound_manager = SoundManager()
        self.running = True
        self.state = "MENU" # MENU, PLAYING, GAME_OVER
        self.game_mode = "2PLAYER"  # "SINGLEPLAYER" oder "2PLAYER"
        self.level = 1
        
        # Partikel für Explosions-Effekte
        self.particles = []
        
        # Hintergrund-Surface für den Spielfeld-Hintergrund
        self.bg_surface = create_background_surface()
        
        # Startbildschirm anzeigen
        self._show_menu()

    def _init_level(self):
        """Initialisiert ein neues Level (oder neues Level bei alle Steine weg)."""
        self.scores = {1: 0, 2: 0}
        self.lives = {1: MAX_LIVES, 2: MAX_LIVES}
        
        # Paddles
        self.paddles = [
            Paddle(SCREEN_WIDTH * 0.25 - PADDLE_WIDTH/2, COLOR_P1, 1),
            Paddle(SCREEN_WIDTH * 0.75 - PADDLE_WIDTH/2, COLOR_P2, 2)
        ]
        
        # Bälle - jeder Spieler startet mit einem Ball in seiner Farbe (noch nicht gestartet)
        self.balls = [
            Ball(self.paddles[0].rect.centerx, self.paddles[0].rect.top - 20, COLOR_P1, 1),
            Ball(self.paddles[1].rect.centerx, self.paddles[1].rect.top - 20, COLOR_P2, 2)
        ]
        
        # Steine Generieren (Zentriert)
        self.bricks = []
        total_width = GRID_COLS * BRICK_WIDTH + (GRID_COLS - 1) * BRICK_PADDING
        start_x = (SCREEN_WIDTH - total_width) // 2
        
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = start_x + col * (BRICK_WIDTH + BRICK_PADDING)
                y = BRICK_OFFSET_TOP + row * (BRICK_HEIGHT + BRICK_PADDING)
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                self.bricks.append(Brick(x, y, color))
        
        # Ball-Start-Indikatoren (wenn Ball noch am Paddle klebt)
        self.ball_ready = {1: False, 2: False}

    def _show_menu(self):
        """Zeigt das Startmenü mit Spielmodus-Auswahl."""
        # Hintergrund
        self.screen.fill(BG_COLOR)
        
        # Subtiler radialer Gradient-Effekt
        for i in range(8):
            alpha = 20 - i * 2
            size = SCREEN_WIDTH - i * 80
            if size > 0:
                rect = pygame.Rect(SCREEN_WIDTH//2 - size//2, SCREEN_HEIGHT//2 - size//2, size, size)
                pygame.draw.rect(self.screen, (20, 20, 60, alpha), rect, border_radius=30)
        
        # Titel mit Glow-Effekt
        title = self.big_font.render("PSYKANOID", True, WHITE)
        glow_surf = pygame.Surface((title.get_width() + 60, title.get_height() + 60), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*COLOR_P1[:3], 25), (glow_surf.get_width()//2, glow_surf.get_height()//2), 60)
        self.screen.blit(glow_surf, (SCREEN_WIDTH//2 - glow_surf.get_width()//2, 60))
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        # Untertitel
        subtitle = self.small_font.render("Ein modernes Breakout-Spiel", True, (180, 180, 200))
        self.screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 150))
        
        # Trennlinie
        pygame.draw.line(self.screen, (50, 50, 80), (300, 180), (724, 180), 2)
        
        # Spielmodus-Auswahl
        mode_label = self.small_font.render("Spielmodus wählen:", True, (200, 200, 220))
        self.screen.blit(mode_label, (SCREEN_WIDTH//2 - mode_label.get_width()//2, 200))
        
        # Singleplayer-Option
        if self.game_mode == "SINGLEPLAYER":
            sp_text = self.font.render("● SINGLEPLAYER", True, COLOR_P1)
            sp_key = self.small_font.render("[ LEERTASTE ]", True, COLOR_P1)
        else:
            sp_text = self.small_font.render("○ SINGLEPLAYER", True, (150, 150, 170))
            sp_key = self.small_font.render("[ H-TASTE ]", True, (150, 150, 170))
        self.screen.blit(sp_text, (SCREEN_WIDTH//2 - sp_text.get_width()//2, 260))
        self.screen.blit(sp_key, (SCREEN_WIDTH//2 - sp_key.get_width()//2, 260 + sp_text.get_height()))
        
        # 2-Player-Option
        if self.game_mode == "2PLAYER":
            p2_text = self.font.render("● 2-PLAYER", True, COLOR_P2)
            p2_key = self.small_font.render("[ LEERTASTE ]", True, COLOR_P2)
        else:
            p2_text = self.small_font.render("○ 2-PLAYER", True, (150, 150, 170))
            p2_key = self.small_font.render("[ N-TASTE ]", True, (150, 150, 170))
        self.screen.blit(p2_text, (SCREEN_WIDTH//2 - p2_text.get_width()//2, 320))
        self.screen.blit(p2_key, (SCREEN_WIDTH//2 - p2_key.get_width()//2, 320 + p2_text.get_height()))
        
        # START-Button
        start_text = self.big_font.render("▶ START", True, (0, 255, 100))
        start_key = self.small_font.render("[ LEERTASTE ]", True, (0, 255, 100))
        self.screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, 430))
        self.screen.blit(start_key, (SCREEN_WIDTH//2 - start_key.get_width()//2, 480))
        
        # Untere Info
        info_text = self.small_font.render("X = Schließen / ESC = Spiel abbrechen", True, (120, 120, 140))
        self.screen.blit(info_text, (SCREEN_WIDTH//2 - info_text.get_width()//2, 550))
        
        pygame.display.flip()

    def draw_ui(self):
        # UI-Hintergrund (transparenter Balken)
        ui_bg = pygame.Surface((SCREEN_WIDTH, 100), pygame.SRCALPHA)
        ui_bg.fill((0, 0, 0, 80))
        self.screen.blit(ui_bg, (0, 0))
        
        # Scores und Leben
        score1_surf = self.font.render(f"P1: {self.scores[1]}", True, COLOR_P1)
        score2_surf = self.font.render(f"P2: {self.scores[2]}", True, COLOR_P2)
        
        # Leben anzeigen (als Herzen-Text)
        lives1_surf = self.small_font.render(f"Leben: {'❤️' * self.lives[1]}", True, COLOR_P1)
        lives2_surf = self.small_font.render(f"Leben: {'❤️' * self.lives[2]}", True, COLOR_P2)
        
        # Level anzeigen
        level_surf = self.small_font.render(f"Level {self.level}", True, (200, 200, 220))
        
        self.screen.blit(score1_surf, (30, 20))
        self.screen.blit(lives1_surf, (30, 60))
        self.screen.blit(score2_surf, (SCREEN_WIDTH - score2_surf.get_width() - 30, 20))
        self.screen.blit(lives2_surf, (SCREEN_WIDTH - lives2_surf.get_width() - 30, 60))
        self.screen.blit(level_surf, (SCREEN_WIDTH//2 - level_surf.get_width()//2, 35))
        
        # Controls
        if self.game_mode == "SINGLEPLAYER":
            ctrl1 = self.small_font.render("P1: A / D", True, (150, 150, 170))
            self.screen.blit(ctrl1, (SCREEN_WIDTH//2 - ctrl1.get_width()//2, SCREEN_HEIGHT - 40))
        else:
            ctrl1 = self.small_font.render("P1: A / D", True, COLOR_P1)
            ctrl2 = self.small_font.render("P2: ← / →", True, COLOR_P2)
            self.screen.blit(ctrl1, (30, SCREEN_HEIGHT - 40))
            self.screen.blit(ctrl2, (SCREEN_WIDTH - ctrl2.get_width() - 30, SCREEN_HEIGHT - 40))

    def handle_collisions(self):
        for ball in self.balls:
            ball_rect = ball.get_rect()

            # --- Wand-Kollisionen ---
            if ball.x - ball.radius <= 0:
                ball.x = ball.radius
                ball.dx *= -1
                self.sound_manager.play('wall_hit')
            elif ball.x + ball.radius >= SCREEN_WIDTH:
                ball.x = SCREEN_WIDTH - ball.radius
                ball.dx *= -1
                self.sound_manager.play('wall_hit')
                
            if ball.y - ball.radius <= 0:
                ball.y = ball.radius
                ball.dy *= -1
                self.sound_manager.play('wall_hit')
            
            # Ball fällt unten raus -> Leben verlieren
            if ball.y > SCREEN_HEIGHT + 50:
                self.sound_manager.play('life_lost')
                
                # Leben abziehen
                self.lives[ball.player_num] -= 1
                
                # Prüfen ob Spieler noch Leben hat
                if self.lives[ball.player_num] > 0:
                    # Ball am entsprechenden Paddle zurücksetzen
                    paddle = self.paddles[ball.player_num - 1]
                    ball.x = paddle.rect.centerx
                    ball.y = paddle.rect.top - 20
                    ball.dx = 0
                    ball.dy = 0
                    ball.launched = False  # Ball klebt wieder am Paddle
                    ball.color = paddle.color
                    continue  # Weiter zum nächsten Ball
                
                # Ball verstecken (Spieler hat kein Leben mehr)
                ball.color = (50, 50, 50)
                ball.dx = 0
                ball.dy = 0
                
                # Prüfen ob Spiel vorbei (beide Spieler ohne Leben)
                if self.lives[1] <= 0 and self.lives[2] <= 0:
                    self.state = "GAME_OVER"
                continue  # Weiter zum nächsten Ball

            # --- Paddle-Kollisionen ---
            for paddle in self.paddles:
                if ball_rect.colliderect(paddle.rect) and ball.dy > 0:
                    self.sound_manager.play('paddle_hit')
                    
                    # Ball bekommt die Farbe des Paddels (letzter Berührer)
                    ball.color = paddle.color
                    ball.player_num = paddle.player_num
                    
                    # Berechne Abprallwinkel basierend auf Trefferposition
                    hit_point = (ball.x - paddle.rect.centerx) / (PADDLE_WIDTH / 2)
                    hit_point = max(-1.0, min(1.0, hit_point)) # Clamping
                    
                    # Max angle = 60 degrees (pi/3)
                    bounce_angle = hit_point * (math.pi / 3)
                    
                    speed = math.sqrt(ball.dx**2 + ball.dy**2)
                    speed = min(speed + 0.2, BASE_BALL_SPEED * 1.5) # Leichte Beschleunigung, max Capped
                    
                    ball.dx = speed * math.sin(bounce_angle)
                    ball.dy = -speed * math.cos(bounce_angle)
                    ball.y = paddle.rect.top - ball.radius # Raussetzen um Steckenbleiben zu verhindern

            # --- Stein-Kollisionen ---
            for brick in self.bricks[:]:
                if ball_rect.colliderect(brick.rect):
                    self.sound_manager.play('brick_hit')
                    
                    # Simple AABB Kollisions-Auflösung
                    overlap_left = ball_rect.right - brick.rect.left
                    overlap_right = brick.rect.right - ball_rect.left
                    overlap_top = ball_rect.bottom - brick.rect.top
                    overlap_bottom = brick.rect.bottom - ball_rect.top
                    
                    min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                    
                    if min_overlap in (overlap_left, overlap_right):
                        ball.dx *= -1
                    else:
                        ball.dy *= -1
                        
                    if brick.hit():
                        self.bricks.remove(brick)
                        self.scores[ball.player_num] += 100
                        # Partikel-Explosion für zerstörte Steine
                        for _ in range(15):
                            self.particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.base_color))
                    else:
                        self.scores[ball.player_num] += 20 # Punkte für Teil-Treffer
                        
                    break # Nur ein Stein pro Frame (verhindert weirdes Durchschlagen)

    def run(self):
        while self.running:
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "PLAYING":
                            self.state = "MENU"
                            self._show_menu()
                        elif self.state == "GAME_OVER":
                            self.state = "MENU"
                            self._show_menu()
                        # Im Menü macht ESC nichts (nur Spiel beenden mit X)
                    if self.state == "MENU":
                        if event.key == pygame.K_SPACE:
                            # Spielmodus starten
                            self.state = "PLAYING"
                            # Level initialisieren
                            self._init_level()
                            # P2 Paddle verstecken (Singleplayer)
                            if self.game_mode == "SINGLEPLAYER":
                                self.paddles[1].rect = pygame.Rect(0, 0, 0, 0)
                                self.balls[1].color = (50, 50, 50)
                                self.balls[1].dx = 0
                                self.balls[1].dy = 0
                            else:
                                # Beide Paddles zeigen (2-Player)
                                self.paddles[1].rect = pygame.Rect(
                                    SCREEN_WIDTH * 0.75 - PADDLE_WIDTH/2,
                                    SCREEN_HEIGHT - 50,
                                    PADDLE_WIDTH,
                                    PADDLE_HEIGHT
                                )
                                self.balls[1].color = COLOR_P2
                        elif event.key == pygame.K_h:  # H für Singleplayer
                            self.game_mode = "SINGLEPLAYER"
                            self._show_menu()
                        elif event.key == pygame.K_n:  # N für 2-Player
                            self.game_mode = "2PLAYER"
                            self._show_menu()
                    if self.state == "GAME_OVER":
                        if event.key == pygame.K_SPACE:
                            # Neues Level starten (im selben Modus)
                            self.level += 1
                            self._init_level()
                            self.state = "PLAYING"
                        elif event.key == pygame.K_ESCAPE:
                            # Zurück zum Menü
                            self.state = "MENU"
                            self._show_menu()

            keys = pygame.key.get_pressed()

            # Update Logik
            if self.state == "PLAYING":
                for paddle in self.paddles:
                    if paddle.rect.width > 0:  # Nur bewegen wenn sichtbar
                        paddle.move(keys)
                
                # Ball-Start-Tasten prüfen (P1: W, P2: O)
                # Nur starten wenn Ball wirklich noch am Paddle klebt (dx=0 und dy=0)
                for i, paddle in enumerate(self.paddles):
                    if paddle.rect.width > 0:  # Nur wenn Paddle sichtbar
                        ball = self.balls[i]
                        if not ball.launched and ball.dx == 0 and ball.dy == 0:
                            if paddle.player_num == 1 and keys[pygame.K_w]:
                                ball.launch()
                            elif paddle.player_num == 2 and keys[pygame.K_o]:  # O statt ↑ (Konflikt mit P2-Steuerung!)
                                ball.launch()
                
                for ball in self.balls:
                    if ball.color != (50, 50, 50):  # Nur aktive Bälle updaten
                        # Finde passendes Paddle für Ball-Positionierung wenn nicht gestartet
                        paddle = None
                        for p in self.paddles:
                            if p.player_num == ball.player_num and p.rect.width > 0:
                                paddle = p
                                break
                        ball.update(paddle)
                
                self.handle_collisions()
                
                # Prüfen ob alle Steine weg -> neues Level
                if len(self.bricks) == 0:
                    self.sound_manager.play('game_over')
                    self.level += 1
                    self._init_level()

            # Render Logik
            if self.state == "MENU":
                # Menü wird bereits in _show_menu() gezeichnet und display.flip() aufgerufen
                pass
            else:
                # Hintergrund mit Gradient
                self.screen.blit(self.bg_surface, (0, 0))
                
                # Partikel updaten und zeichnen
                for particle in self.particles[:]:
                    particle.update()
                    particle.draw(self.screen)
                    if particle.life <= 0:
                        self.particles.remove(particle)
                
                # Mittellinie (dekorativ)
                line_color = (50, 50, 70)
                for i in range(0, SCREEN_HEIGHT, 20):
                    if i % 40 < 20:
                        pygame.draw.line(self.screen, line_color, (SCREEN_WIDTH//2, i), (SCREEN_WIDTH//2, i + 10), 2)
                
                for brick in self.bricks:
                    brick.draw(self.screen)
                for paddle in self.paddles:
                    if paddle.rect.width > 0:  # Nur zeichnen wenn sichtbar
                        paddle.draw(self.screen)
                for ball in self.balls:
                    if ball.color != (50, 50, 50):  # Nur zeichnen wenn aktiv
                        ball.draw(self.screen)
                        # Ball-Start-Indikator wenn Ball noch am Paddle klebt
                        if not ball.launched:
                            # "Drücke W" oder "Drücke O" Text über dem Ball
                            if ball.player_num == 1:
                                launch_text = self.small_font.render("Drücke W", True, WHITE)
                            else:
                                launch_text = self.small_font.render("Drücke O", True, WHITE)
                            text_rect = launch_text.get_rect(center=(int(ball.x), int(ball.y - 30)))
                            self.screen.blit(launch_text, text_rect)
                
                self.draw_ui()
            
            if self.state == "GAME_OVER":
                # Hintergrund mit Gradient
                self.screen.blit(self.bg_surface, (0, 0))
                
                # Partikel updaten und zeichnen
                for particle in self.particles[:]:
                    particle.update()
                    particle.draw(self.screen)
                    if particle.life <= 0:
                        self.particles.remove(particle)
                
                # Mittellinie (dekorativ)
                line_color = (50, 50, 70)
                for i in range(0, SCREEN_HEIGHT, 20):
                    if i % 40 < 20:
                        pygame.draw.line(self.screen, line_color, (SCREEN_WIDTH//2, i), (SCREEN_WIDTH//2, i + 10), 2)
                
                # Steine noch anzeigen (falls gewünscht)
                for brick in self.bricks:
                    brick.draw(self.screen)
                for paddle in self.paddles:
                    if paddle.rect.width > 0:
                        paddle.draw(self.screen)
                
                # Overlay
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                self.screen.blit(overlay, (0, 0))
                
                # Gewinner ermitteln
                winner = "UNENTSCHIEDEN"
                if self.lives[1] > 0 and self.lives[2] <= 0:
                    winner = "SPIELER 1 GEWINNT!"
                elif self.lives[2] > 0 and self.lives[1] <= 0:
                    winner = "SPIELER 2 GEWINNT!"
                elif self.scores[1] > self.scores[2]:
                    winner = "SPIELER 1 GEWINNT!"
                elif self.scores[2] > self.scores[1]:
                    winner = "SPIELER 2 GEWINNT!"
                
                # Text rendern
                win_text = self.big_font.render(winner, True, WHITE)
                score_text1 = self.small_font.render(f"P1: {self.scores[1]} Punkte", True, COLOR_P1)
                score_text2 = self.small_font.render(f"P2: {self.scores[2]} Punkte", True, COLOR_P2)
                level_text = self.small_font.render(f"Level {self.level} erreicht", True, (200, 200, 200))
                
                if self.game_mode == "SINGLEPLAYER":
                    restart_text = self.small_font.render("LEERTASTE = Nächstes Level", True, WHITE)
                    menu_text = self.small_font.render("ESC = Hauptmenü", True, (200, 200, 200))
                else:
                    restart_text = self.small_font.render("LEERTASTE = Neues Spiel", True, WHITE)
                    menu_text = self.small_font.render("ESC = Hauptmenü", True, (200, 200, 200))
                
                # Text positionieren
                self.screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, SCREEN_HEIGHT//2 - 140))
                self.screen.blit(level_text, (SCREEN_WIDTH//2 - level_text.get_width()//2, SCREEN_HEIGHT//2 - 80))
                self.screen.blit(score_text1, (SCREEN_WIDTH//2 - score_text1.get_width()//2 - 100, SCREEN_HEIGHT//2 - 30))
                self.screen.blit(score_text2, (SCREEN_WIDTH//2 - score_text2.get_width()//2 + 50, SCREEN_HEIGHT//2 - 30))
                self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 30))
                self.screen.blit(menu_text, (SCREEN_WIDTH//2 - menu_text.get_width()//2, SCREEN_HEIGHT//2 + 70))

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
