import pygame

class AnimatedSprite:
    """
    Crea una animación a partir de un sprite sheet horizontal.
    Asume frames cuadrados: frame_w = surface.get_height()
    fps: frames por segundo de la animación.
    """
    def __init__(self, sheet_surf: pygame.Surface, fps: int = 8, frame_w: int = None):
        self.sheet = sheet_surf
        self.fps = fps
        self.last_update = pygame.time.get_ticks()
        self.frame_time = 1000 // max(1, fps)

        # determinar tamaño del frame
        h = self.sheet.get_height()
        self.frame_w = frame_w or h
        total_w = self.sheet.get_width()
        self.frames = []
        if self.frame_w <= 0:
            raise ValueError("frame_w inválido")
        cols = max(1, total_w // self.frame_w)
        for i in range(cols):
            rect = pygame.Rect(i * self.frame_w, 0, self.frame_w, h)
            frame = pygame.Surface((self.frame_w, h), pygame.SRCALPHA)
            frame.blit(self.sheet, (0, 0), rect)
            self.frames.append(frame)
        if not self.frames:
            # fallback: usar la sheet entera
            self.frames = [self.sheet.copy()]

        self.index = 0

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update >= self.frame_time:
            self.index = (self.index + 1) % len(self.frames)
            self.last_update = now

    def get_frame(self) -> pygame.Surface:
        return self.frames[self.index]

    def reset(self):
        self.index = 0
        self.last_update = pygame.time.get_ticks()

    def tinted(self, color):
        """
        Devuelve una nueva lista de frames tinted (copia) con overlay del color.
        Útil si quieres varias variantes coloreadas del mismo sheet.
        """
        out_frames = []
        for f in self.frames:
            copy = f.copy()
            tint = pygame.Surface(copy.get_size(), pygame.SRCALPHA)
            tint.fill((*color, 80))  # alpha pequeño para mezclar
            copy.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            out_frames.append(copy)
        ret = AnimatedSprite.__new__(AnimatedSprite)
        ret.sheet = None
        ret.fps = self.fps
        ret.last_update = pygame.time.get_ticks()
        ret.frame_time = self.frame_time
        ret.frame_w = self.frame_w
        ret.frames = out_frames
        ret.index = 0
        return ret
