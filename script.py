import pygame
import numpy as np
import sounddevice as sd

# Einstellungen
WIDTH, HEIGHT = 600, 600
CENTER = (WIDTH // 2, HEIGHT // 2)
RADIUS = 15

# Audio-Einstellungen
fs = 44100  # Sampling Frequency
duration = 10  # seconds
frequency = 440  # Hz

# Generiere ein Dauerton (Sinus)
t = np.linspace(0, duration, int(fs * duration), endpoint=False)
audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)

# Initialisierung
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Audio Demo")
clock = pygame.time.Clock()

# Startposition des Punktes
pos = list(CENTER)
dragging = False

def get_panning_and_volume(x, y):
    # x: -1 (links) bis 1 (rechts), y: -1 (vorne) bis 1 (hinten)
    rel_x = (x - CENTER[0]) / (WIDTH // 2)
    rel_y = (y - CENTER[1]) / (HEIGHT // 2)
    # Panning
    left = max(0, 1 - rel_x)
    right = max(0, 1 + rel_x)
    # Lautstärke: weiter hinten = leiser
    volume = max(0.2, 1 - abs(rel_y) * 0.7)
    # Normiere Panning
    total = left + right
    left, right = left / total, right / total
    return left * volume, right * volume

def make_stereo(audio, left, right):
    stereo = np.zeros((audio.shape[0], 2), dtype=np.float32)
    stereo[:, 0] = audio * left
    stereo[:, 1] = audio * right
    return stereo

# Audio-Callback
cur_left, cur_right = 0.5, 0.5
def audio_callback(outdata, frames, time, status):
    global audio_pos, cur_left, cur_right
    chunk = audio[audio_pos:audio_pos+frames]
    if len(chunk) < frames:
        chunk = np.pad(chunk, (0, frames - len(chunk)))
    stereo = make_stereo(chunk, cur_left, cur_right)
    outdata[:] = stereo
    audio_pos += frames
    if audio_pos >= len(audio):
        audio_pos = 0

audio_pos = 0
stream = sd.OutputStream(channels=2, callback=audio_callback, samplerate=fs, blocksize=1024)
stream.start()

# Main Loop
running = True
while running:
    clock.tick(60)
    screen.fill((30, 30, 30))

    # Markierungen
    pygame.draw.line(screen, (80, 80, 80), (CENTER[0], 0), (CENTER[0], HEIGHT), 2)
    pygame.draw.line(screen, (80, 80, 80), (0, CENTER[1]), (WIDTH, CENTER[1]), 2)
    font = pygame.font.SysFont(None, 24)
    screen.blit(font.render("Vorne", True, (200,200,200)), (CENTER[0]-25, 10))
    screen.blit(font.render("Hinten", True, (200,200,200)), (CENTER[0]-30, HEIGHT-30))
    screen.blit(font.render("Links", True, (200,200,200)), (10, CENTER[1]-10))
    screen.blit(font.render("Rechts", True, (200,200,200)), (WIDTH-60, CENTER[1]-10))
    screen.blit(font.render("Mitte", True, (255,255,0)), (CENTER[0]-22, CENTER[1]-30))

    # Punkt zeichnen
    pygame.draw.circle(screen, (0, 200, 255), pos, RADIUS)

    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if np.hypot(pos[0] - event.pos[0], pos[1] - event.pos[1]) < RADIUS:
                dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False
        elif event.type == pygame.MOUSEMOTION and dragging:
            pos[0], pos[1] = event.pos
            pos[0] = min(max(pos[0], 0), WIDTH)
            pos[1] = min(max(pos[1], 0), HEIGHT)

    # Update Audio
    cur_left, cur_right = get_panning_and_volume(pos[0], pos[1])

    pygame.display.flip()

pygame.quit()
stream.stop()
stream.close()
