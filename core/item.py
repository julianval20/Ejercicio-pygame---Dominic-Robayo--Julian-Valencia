import pygame
import random
import time
from settings import ANCHO, ALTO, COLOR_ITEM, ALTURA_SUELO

class Item:
    """
    Ítem simple: rectángulo que se mueve hacia la izquierda.
    Tipos: escudo, reduccion, invulnerable, misterioso
    """

    def __init__(self):
        tipos = random.choices(
            ["escudo", "reduccion", "invulnerable", "misterioso"],
            weights=[2, 2, 1, 3],
            k=1
        )
        self.tipo = tipos[0]

        # Posición: a la derecha de la pantalla, alineado verticalmente
        ancho_item = 30
        x = ANCHO + random.randint(0, 200)
        # Centrar con respecto al jugador (suponiendo tamaño 95)
        centro_y = ALTO - ALTURA_SUELO - 95 // 2 - (ancho_item // 2)
        y = centro_y

        self.rect = pygame.Rect(x, y, ancho_item, ancho_item)
        self.velocidad = 6
        self.anim_frame = 0
        self.anim_tiempo = time.time()

    def mover(self, velocidad_juego):
        self.rect.x -= int(velocidad_juego)

    def dibujar(self, ventana):
        color = self.obtener_color()
        if self.tipo == "misterioso":
            if time.time() - self.anim_tiempo > 0.12:
                self.anim_frame = (self.anim_frame + 1) % 3
                self.anim_tiempo = time.time()
            colores = [(255, 0, 255), (255, 255, 0), (0, 255, 255)]
            pygame.draw.rect(ventana, colores[self.anim_frame], self.rect)
        else:
            pygame.draw.rect(ventana, color, self.rect)

    def obtener_color(self):
        colores = {
            "escudo": (0, 180, 255),
            "reduccion": (0, 255, 0),
            "invulnerable": (255, 215, 0),
            "misterioso": (255, 0, 255)
        }
        return colores.get(self.tipo, COLOR_ITEM)
