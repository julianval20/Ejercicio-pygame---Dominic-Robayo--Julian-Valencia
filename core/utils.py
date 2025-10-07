import pygame

def dibujar_texto(ventana, texto, fuente, color, pos):
    x, y = pos
    surf = fuente.render(str(texto), True, color)
    ventana.blit(surf, (x, y))
