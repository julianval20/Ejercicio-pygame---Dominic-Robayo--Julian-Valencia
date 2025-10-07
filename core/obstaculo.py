# core/obstaculo.py
import pygame
import random
import os
from settings import ANCHO, ALTO, ALTURA_SUELO, COLOR_OBSTACULO

# posible(s) ubicación(es) para la imagen de obstáculo "1.png"
_POSSIBLE_OBSTACLE_PATHS = [
    os.path.join("assets", "obstacles", "1.png"),
    os.path.join("assets", "1.png"),
    os.path.join("assets", "players", "1.png"),
]

class Obstaculo:
    """
    Obstáculo rectangular; puede ser 'suelo' (desde el suelo hacia arriba)
    o 'techo' (desde la parte superior hacia abajo, dejando un hueco).

    Ahora intenta usar la imagen '1.png' escalada al tamaño del obstáculo.
    Si la imagen no está disponible o falla la carga, usa el rectángulo de color.
    """
    def __init__(self, tipo, offset_x=0):
        self.tipo = tipo
        self.color = COLOR_OBSTACULO
        self.velocidad = 8
        self.image = None  # Surface si se carga la imagen, None si no

        if self.tipo == "suelo":
            # Ancho/alto razonables para obstáculo de suelo
            self.ancho = random.randint(70, 100)
            # altura del obstáculo (debe ser pasable saltando)
            self.alto = random.randint(90, 130)
            self.x = ANCHO + offset_x
            self.y = ALTO - ALTURA_SUELO - self.alto

        elif self.tipo == "techo":
            # Hueco exacto: el obstáculo parte desde el techo y baja hasta casi el suelo,
            # dejando un hueco para el jugador agachado.
            hueco = 60  # espacio libre desde el suelo hacia arriba (ajustable)
            self.ancho = random.randint(70, 100)
            self.alto = ALTO - ALTURA_SUELO - hueco
            self.x = ANCHO + offset_x
            self.y = 0

        else:
            # fallback
            self.ancho = 80
            self.alto = 100
            self.x = ANCHO + offset_x
            self.y = ALTO - ALTURA_SUELO - self.alto

        self.rect = pygame.Rect(self.x, self.y, self.ancho, self.alto)

        # Intentar cargar la imagen '1.png' y escalarla al tamaño (ancho x alto).
        # Hacemos esto aquí (en __init__) para evitar errores antes de set_mode.
        self._try_load_image()

    def _try_load_image(self):
        """Intenta cargar la imagen desde varias rutas; si falla, self.image queda None."""
        for p in _POSSIBLE_OBSTACLE_PATHS:
            try:
                if os.path.isfile(p):
                    surf = pygame.image.load(p).convert_alpha()
                    # escalar a tamaño del rect
                    if surf.get_width() > 0 and surf.get_height() > 0:
                        surf_scaled = pygame.transform.smoothscale(surf, (self.ancho, self.alto))
                        self.image = surf_scaled
                        return
            except Exception as e:
                # no abortamos: seguimos intentando otras rutas o quedamos en None
                print(f"[WARN] fallo cargando imagen de obstáculo '{p}': {e}")
                self.image = None
        # si ninguna ruta funcionó, dejamos self.image = None (fallback rect)

    def mover(self, velocidad_juego=8):
        self.rect.x -= int(velocidad_juego)

    def dibujar(self, ventana):
        if self.image:
            try:
                ventana.blit(self.image, self.rect.topleft)
            except Exception:
                # en caso de cualquier problema al blitear, dibujamos el rect de color
                pygame.draw.rect(ventana, self.color, self.rect)
        else:
            pygame.draw.rect(ventana, self.color, self.rect)
