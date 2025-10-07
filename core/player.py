# core/player.py
import pygame
from settings import ALTO, ALTURA_SUELO, COLOR_JUGADOR

def _lowest_nontransparent_row(surf: pygame.Surface) -> int:
    w, h = surf.get_size()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            try:
                if surf.get_at((x, y))[3] != 0:
                    return y
            except Exception:
                return h - 1
    return h - 1

class Player:
    """
    Soporta animaciones (dict de AnimatedSprite) o Surface estática.
    set_sprite(surf_or_dict, scale_factor=None) permite ajustar tamaño visual.
    """

    def __init__(self):
        self.tamano_original = 95
        self.tamano = self.tamano_original
        self.rect = pygame.Rect(100, ALTO - ALTURA_SUELO - self.tamano, self.tamano, self.tamano)
        self.color = COLOR_JUGADOR

        # Física
        self.velocidad_y = 0.0
        self.gravedad = 1.2
        self.en_suelo = True

        # Estados
        self.agachado = False

        # Sprites/animaciones
        self.animations = None
        self.static_sprite = None
        self.sprite_offset = (0, 0)
        self.current_anim_key = "idle"

    def manejar_eventos(self, keys):
        # Saltar
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.en_suelo and not self.agachado:
            self.velocidad_y = -22
            self.en_suelo = False

        # Agacharse: solo en suelo
        if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.en_suelo:
            if not self.agachado:
                altura_reducida = max(20, int(self.tamano_original * 0.55))
                bottom = self.rect.bottom
                self.rect.height = altura_reducida
                self.rect.bottom = bottom
                self.agachado = True
        else:
            if self.agachado:
                bottom = self.rect.bottom
                self.rect.height = self.tamano_original
                self.rect.bottom = bottom
                self.agachado = False

    def mover(self):
        self.rect.y += int(self.velocidad_y)

        if not self.en_suelo:
            self.velocidad_y += self.gravedad
            if self.velocidad_y > 40:
                self.velocidad_y = 40

        ground_y = ALTO - ALTURA_SUELO
        if self.rect.bottom >= ground_y:
            self.rect.bottom = ground_y
            self.en_suelo = True
            self.velocidad_y = 0

        if self.rect.left < 0:
            self.rect.left = 0

        # elegir animación
        if self.animations:
            if not self.en_suelo:
                if self.velocidad_y < 0 and "jump" in self.animations:
                    self.current_anim_key = "jump"
                elif "fall" in self.animations:
                    self.current_anim_key = "fall"
            else:
                if self.agachado and "roll" in self.animations:
                    self.current_anim_key = "roll"
                else:
                    if "run" in self.animations and not self.agachado:
                        self.current_anim_key = "run"
                    else:
                        self.current_anim_key = "idle"

    def dibujar(self, ventana):
        # sombra simple
        try:
            sombra_w = max(1, self.rect.width)
            sombra_h = max(6, self.rect.height // 8)
            sombra_surf = pygame.Surface((sombra_w, sombra_h), pygame.SRCALPHA)
            sombra_surf.fill((0, 0, 0, 100))
            sombra_pos = (self.rect.left, self.rect.bottom - sombra_h // 2)
            ventana.blit(sombra_surf, sombra_pos)
        except Exception:
            pass

        if self.animations:
            anim = self.animations.get(self.current_anim_key)
            if anim:
                try:
                    anim.update()
                    frame = anim.get_frame()
                    fw, fh = frame.get_width(), frame.get_height()
                    scale = self.rect.height / fh if fh > 0 else 1.0
                    new_w = max(1, int(fw * scale))
                    new_h = max(1, int(fh * scale))
                    img = pygame.transform.smoothscale(frame, (new_w, new_h))

                    # corregir padding inferior del frame para alinear "pies"
                    baseline_row = _lowest_nontransparent_row(frame)
                    baseline_offset = (fh - 1 - baseline_row)
                    baseline_offset_scaled = int(baseline_offset * scale)

                    sx, sy = self.sprite_offset
                    draw_x = self.rect.left + sx + (self.rect.width - new_w) // 2
                    draw_y = self.rect.bottom - new_h + sy + baseline_offset_scaled

                    ventana.blit(img, (draw_x, draw_y))
                except Exception:
                    pygame.draw.rect(ventana, self.color, self.rect)
            else:
                pygame.draw.rect(ventana, self.color, self.rect)
        elif self.static_sprite:
            try:
                img = pygame.transform.smoothscale(self.static_sprite, (self.rect.width, self.rect.height))
                sx, sy = self.sprite_offset
                ventana.blit(img, (self.rect.left + sx, self.rect.top + sy))
            except Exception:
                pygame.draw.rect(ventana, self.color, self.rect)
        else:
            pygame.draw.rect(ventana, self.color, self.rect)

        # Nota: ya no dibujamos el borde blanco al agacharnos (solicitado)

    def set_sprite(self, surf_or_dict, scale_factor: float | None = None):
        if isinstance(surf_or_dict, dict):
            self.animations = surf_or_dict
            self.static_sprite = None
            max_frame_h = 0
            for a in self.animations.values():
                try:
                    a.reset()
                    if hasattr(a, "frames") and a.frames:
                        h = a.frames[0].get_height()
                        if h > max_frame_h:
                            max_frame_h = h
                except Exception:
                    pass
            if max_frame_h > 0:
                factor = scale_factor if (scale_factor is not None) else 1.8
                nuevo_alto = max(60, int(max_frame_h * factor))
                self.tamano_original = nuevo_alto
            bottom = self.rect.bottom
            self.rect.height = self.tamano_original
            self.rect.bottom = bottom
            self.current_anim_key = "idle" if "idle" in self.animations else (next(iter(self.animations)) if self.animations else "idle")
        else:
            self.static_sprite = surf_or_dict
            self.animations = None
            try:
                h = surf_or_dict.get_height()
                if h and h > 0:
                    factor = scale_factor if (scale_factor is not None) else 1.8
                    nuevo_alto = max(60, int(h * factor))
                    self.tamano_original = nuevo_alto
                    bottom = self.rect.bottom
                    self.rect.height = self.tamano_original
                    self.rect.bottom = bottom
            except Exception:
                pass

    def set_color(self, rgb):
        self.color = rgb
