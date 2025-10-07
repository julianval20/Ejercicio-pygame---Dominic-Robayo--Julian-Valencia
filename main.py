# main.py
import pygame
import sys
import random
import os
from settings import ANCHO, ALTO, COLOR_FONDO, COLOR_SUELO, ALTURA_SUELO
from core.player import Player
from core.obstaculo import Obstaculo
from core.item import Item
from core.utils import dibujar_texto
from core.sprites import AnimatedSprite

pygame.init()

# directorio donde están los sheets
SPRITE_DIR = os.path.join("assets", "players")

# definición de personajes y sus sheets (nombres exactos de los archivos)
CHAR_SHEETS = {
    "Cat": {
        "idle": "1_Cat_Idle-Sheet.png",
        "run":  "2_Cat_Run-Sheet.png",
        "jump": "3_Cat_Jump-Sheet.png",
        "fall": "4_Cat_Fall-Sheet.png",
    },
    "Male": {
        # mapeo: slide -> roll (usado cuando el jugador se agacha)
        "run":   "male_hero-walk.png",
        "jump":  "male_hero-jump.png",
        "fall":  "male_hero-fall.png",
        "roll":  "male_hero-slide.png",
        "death": "male_hero-death.png",
    }
}
# al principio de main.py, junto a CHAR_SHEETS o FALLBACK_COLORS
SCALE_BY_CHAR = {
    "Cat": 3.1,    # aumenté para que el gato no se vea pequeño
    "Male": 2.2,   # male un poco más pequeño que el gato, ajusta si quieres
}


# fallback de color si no hay sprite
FALLBACK_COLORS = {
    "Azul": (95, 95, 220),
    "Cian": (0, 180, 255),
    "Verde": (0, 200, 100),
    "Dorado": (255, 215, 0),
    "Rosado": (255, 120, 120),
    "Morado": (180, 0, 255),
}

# BACKGROUND (parallax)
BG_DIR = os.path.join("assets", "background")
BG_FILES = ["capa1.png", "capa2.png", "capa3.png", "capa4.png"]
# parallax factor por capa: menor = más atrás (se mueve más lento)
BG_FACTORS = [0.25, 0.45, 0.7, 1.0]


# contenedor por personaje -> key -> AnimatedSprite or None (se llenará dentro de main)
ANIM_BY_CHAR = {}

_ICON_FONT = pygame.font.SysFont(None, 18)


def dibujar_icono_poder(ventana, jugador_rect, texto, color, offset_x=0, inside=False):
    w, h = 28, 18
    if inside:
        x = jugador_rect.right - w - 6 + offset_x
        y = jugador_rect.top + 6
    else:
        x = jugador_rect.centerx - w // 2 + offset_x
        y = jugador_rect.top - 26
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((*color, 220))
    ventana.blit(surf, (x, y))
    label = _ICON_FONT.render(texto, True, (0, 0, 0))
    ventana.blit(label, (x + (w - label.get_width()) // 2, y + (h - label.get_height()) // 2))


def dibujar_game_over(ventana, fuente, tiempo_segundos, nivel, record_tiempo, record_nivel):
    overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    ventana.blit(overlay, (0, 0))

    box_width, box_height = 800, 460
    box_x = (ANCHO - box_width) // 2
    box_y = (ALTO - box_height) // 2
    caja = pygame.Rect(box_x, box_y, box_width, box_height)

    pygame.draw.rect(ventana, (18, 18, 18), caja, border_radius=16)
    pygame.draw.rect(ventana, (220, 220, 220), caja, 3, border_radius=16)

    fuente_titulo = pygame.font.SysFont(None, 64)
    titulo_surf = fuente_titulo.render("GAME OVER", True, (255, 80, 80))
    ventana.blit(titulo_surf, (ANCHO // 2 - titulo_surf.get_width() // 2, box_y + 20))

    pygame.draw.line(ventana, (200, 200, 200),
                     (box_x + 48, box_y + 100), (box_x + box_width - 48, box_y + 100), 2)

    fuente_info = pygame.font.SysFont(None, 30)
    gap_y = 40
    start_x = box_x + 60
    start_y = box_y + 130

    ventana.blit(fuente_info.render(f"Tiempo sobrevivido: {tiempo_segundos}s", True, (230, 230, 230)),
                 (start_x, start_y))
    ventana.blit(fuente_info.render(f"Nivel alcanzado: {nivel}", True, (230, 230, 230)),
                 (start_x, start_y + gap_y))
    ventana.blit(fuente_info.render(f"Récord tiempo (s): {record_tiempo}", True, (170, 255, 170)),
                 (start_x, start_y + gap_y * 2))
    ventana.blit(fuente_info.render(f"Récord nivel: {record_nivel}", True, (170, 255, 170)),
                 (start_x, start_y + gap_y * 3))

    fuente_instr = pygame.font.SysFont(None, 26)
    instr_base_y = box_y + 140
    instrucciones = [
        ("Pulsa R para reintentar", (200, 200, 255)),
        ("Pulsa T para ver el tutorial", (255, 200, 200)),
        ("Pulsa ESC para salir", (200, 200, 200))
    ]
    instr_x_right = box_x + box_width - 60
    for i, (txt, col) in enumerate(instrucciones):
        surf = fuente_instr.render(txt, True, col)
        ventana.blit(surf, (instr_x_right - surf.get_width(), instr_base_y + i * 36))

    nota = "Presiona la tecla correspondiente para continuar"
    nota_surf = pygame.font.SysFont(None, 20).render(nota, True, (160, 160, 160))
    ventana.blit(nota_surf, (ANCHO // 2 - nota_surf.get_width() // 2, box_y + box_height - 40))


# Añadido: tope para previews en selección
PREVIEW_MAX_SCALE = 3.5  # no escales más de esto en la selección

def elegir_personaje_multiple(ventana, fuente):
    """
    Muestra tarjetas para seleccionar entre los personajes definidos en CHAR_SHEETS.
    Devuelve (nombre_char, anim_dict_or_surface) donde anim_dict tiene AnimatedSprite values.
    """
    reloj = pygame.time.Clock()
    personajes = list(CHAR_SHEETS.keys())
    seleccion = 0

    # Layout: tarjetas horizontales centradas
    box_w, box_h = 260, 260
    gap = 60
    total_w = len(personajes) * box_w + (len(personajes) - 1) * gap
    start_x = (ANCHO - total_w) // 2
    y = ALTO // 2 - box_h // 2 - 20

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RIGHT:
                    seleccion = (seleccion + 1) % len(personajes)
                elif e.key == pygame.K_LEFT:
                    seleccion = (seleccion - 1) % len(personajes)
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    chosen = personajes[seleccion]
                    anims = {k: v for k, v in ANIM_BY_CHAR.get(chosen, {}).items() if v}
                    if anims:
                        return chosen, anims
                    else:
                        # fallback surface si no hay animaciones
                        s = pygame.Surface((95, 95), pygame.SRCALPHA)
                        s.fill((120, 120, 255))
                        return chosen, s
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                for i, name in enumerate(personajes):
                    rect_x = start_x + i * (box_w + gap)
                    rect = pygame.Rect(rect_x, y, box_w, box_h)
                    if rect.collidepoint(mx, my):
                        anims = {k: v for k, v in ANIM_BY_CHAR.get(name, {}).items() if v}
                        if anims:
                            return name, anims
                        else:
                            s = pygame.Surface((95, 95), pygame.SRCALPHA)
                            s.fill((120, 120, 255))
                            return name, s

        ventana.fill(COLOR_FONDO)
        dibujar_texto(ventana, "Selecciona un personaje (Usa las flechas para seleccionar, Enter/Espacio para confirmar)", fuente, (255, 255, 255), (ANCHO//2 - 420, 60))

        for i, name in enumerate(personajes):
            rect_x = start_x + i * (box_w + gap)
            rect = pygame.Rect(rect_x, y, box_w, box_h)
            pygame.draw.rect(ventana, (36, 36, 36), rect, border_radius=14)

            # elegir animación de preview preferida:
            # intentamos 'idle' -> 'run' -> 'jump' -> any available
            anims = ANIM_BY_CHAR.get(name, {})
            preview = None
            for pref in ("idle", "run", "jump", "fall", "roll"):
                if anims.get(pref):
                    preview = anims[pref]
                    break
            if preview:
                preview.update()
                frame = preview.get_frame()
                fw, fh = frame.get_width(), frame.get_height()
                if fw == 0 or fh == 0:
                    # fallback si algo raro pasa
                    s = pygame.Surface((95, 95), pygame.SRCALPHA)
                    s.fill((100, 100, 100))
                    ventana.blit(s, (rect.centerx - 95//2, rect.centery - 95//2))
                else:
                    max_w = int(box_w * 0.9)
                    max_h = int(box_h * 0.9)
                    base_scale = min(max_w / fw, max_h / fh)
                    # aplicar scale por personaje (para aumentar previews)
                    char_scale = SCALE_BY_CHAR.get(name, 1.8)
                    final_scale = base_scale * char_scale
                    # limitar la escala máxima
                    final_scale = min(final_scale, PREVIEW_MAX_SCALE)
                    new_w = max(1, int(fw * final_scale))
                    new_h = max(1, int(fh * final_scale))
                    img = pygame.transform.smoothscale(frame, (new_w, new_h))
                    ventana.blit(img, (rect.centerx - new_w // 2, rect.centery - new_h // 2))
            else:
                # fallback rectangle
                s = pygame.Surface((95, 95), pygame.SRCALPHA)
                s.fill((100, 100, 100))
                ventana.blit(s, (rect.centerx - 95//2, rect.centery - 95//2))

            # etiqueta
            dibujar_texto(ventana, name, fuente, (220, 220, 220), (rect.centerx - 30, rect.bottom + 8))

            # borde selección
            if i == seleccion:
                pygame.draw.rect(ventana, (255, 255, 255), rect, 3, border_radius=14)
                outer = rect.inflate(14, 14)
                pygame.draw.rect(ventana, (255, 200, 100), outer, 2, border_radius=16)

        pygame.display.flip()
        reloj.tick(30)


def mostrar_tutorial(ventana, fuente_tuto, fuente, record_tiempo, record_nivel):
    # <-- función restaurada exactamente como me pediste (copiada del archivo que pegaste)
    reloj = pygame.time.Clock()
    mostrar = True
    while mostrar:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        keys = pygame.key.get_pressed()
        ventana.fill(COLOR_FONDO)

        dibujar_texto(ventana, "TUTORIAL - Skater Survival", fuente, (255, 255, 255), (40, 30))
        dibujar_texto(ventana, "Controles:", fuente_tuto, (230, 230, 230), (40, 80))
        dibujar_texto(ventana, "- Espacio: Saltar", fuente_tuto, (200, 200, 200), (60, 110))
        dibujar_texto(ventana, "- Flecha abajo: Agacharse", fuente_tuto, (200, 200, 200), (60, 140))
        dibujar_texto(ventana, "- R: Reiniciar cuando pierdas", fuente_tuto, (200, 200, 200), (60, 170))

        dibujar_texto(ventana, "Caja misteriosa puede dar:", fuente_tuto, (255, 255, 255), (40, 220))
        poderes_misterio = [
            ("Escudo", "Te protege de 1 golpe; al romperse te da 2s de invulnerabilidad (texto azul)"),
            ("Reducción", "Baja 1 nivel y reduce velocidad ligeramente (resplandor verde)"),
            ("Invulnerable", "Te hace invencible 10 segundos (texto dorado)"),
            ("Subir nivel", "Sube 1 nivel (resplandor rojo) — aumenta dificultad"),
            ("Desvalijado", "Elimina todos los poderes apilados (resplandor rojo y texto '¡Desvalijado!')"),
        ]
        y = 255
        for nombre, desc in poderes_misterio:
            dibujar_texto(ventana, f"- {nombre}: {desc}", fuente_tuto, (200, 200, 200), (60, y))
            y += 30

        x_right = ANCHO - 420 if ANCHO > 500 else ANCHO - 320
        dibujar_texto(ventana, "Poderes (visual):", fuente_tuto, (255, 255, 255), (x_right, 80))
        rects = [
            ("Escudo", (0, 180, 255)),
            ("Reducción", (0, 255, 0)),
            ("Invulnerable", (255, 215, 0)),
            ("Misteriosa", (180, 0, 255)),
            ("Desvalijado", (255, 0, 0))
        ]
        yy = 110
        for n, c in rects:
            pygame.draw.rect(ventana, c, (x_right, yy, 30, 30))
            dibujar_texto(ventana, n, fuente_tuto, (230, 230, 230), (x_right + 40, yy + 5))
            yy += 40

        dibujar_texto(ventana, f"Récord tiempo (s): {record_tiempo}", fuente_tuto, (255, 255, 255), (x_right, 320))
        dibujar_texto(ventana, f"Récord nivel: {record_nivel}", fuente_tuto, (255, 255, 255), (x_right, 350))

        dibujar_texto(ventana, "Pulsa ESPACIO para comenzar", fuente, (255, 200, 0), (40, ALTO - 80))

        pygame.display.flip()
        if keys[pygame.K_SPACE]:
            mostrar = False
        reloj.tick(30)


def dibujar_background(ventana, bg_layers, velocidad, dt):
    """
    Dibuja y avanza las capas. Cada capa usa su 'surf_scaled' (pre-escalada para cubrir al menos ANCHOxALTO).
    dt no es crítico aquí (puedes pasar 1 por frame), pero permite suavizar.
    """
    if not bg_layers:
        return
    for layer in bg_layers:
        if not layer:
            continue
        # usamos la versión escalada si está disponible
        surf = layer.get("surf_scaled", layer.get("surf"))
        if surf is None:
            continue
        w = layer.get("w_scaled", surf.get_width())
        h = layer.get("h_scaled", surf.get_height())
        factor = layer.get("factor", 0.5)
        # mover offset (mueve hacia la izquierda; sumamos y luego dibujamos -offset)
        layer["offset"] = (layer.get("offset", 0.0) + velocidad * factor * dt) % w

        offset = layer["offset"]

        # alineamos verticalmente: intentamos colocar la base de la imagen pegada al fondo
        # si la imagen es mayor o igual que la pantalla, la dibujamos en y=0, si es menor la pegamos abajo.
        if h >= ALTO:
            y = 0
        else:
            y = ALTO - h

        # tiling horizontal: dibujar suficientes copias para cubrir la pantalla
        start_x = -int(offset)
        x = start_x
        # dibujamos copias hasta cubrir la pantalla (y una extra)
        while x < ANCHO:
            ventana.blit(surf, (x, y))
            x += w
        # copia extra a la izquierda
        ventana.blit(surf, (start_x - w, y))


def generar_obstaculos(obstaculos, tiempo, tiempo_ultimo_spawn):
    if tiempo - tiempo_ultimo_spawn < 35:
        return tiempo_ultimo_spawn

    tipo = random.choice(["techo", "suelo"])
    if tipo == "techo":
        num_bloque = random.randint(1, 5)
        x_offset = 0
        for _ in range(num_bloque):
            nuevo = Obstaculo("techo", offset_x=x_offset)
            obstaculos.append(nuevo)
            x_offset += nuevo.ancho
        tiempo_ultimo_spawn = tiempo + 25
    else:
        obstaculos.append(Obstaculo("suelo"))
        tiempo_ultimo_spawn = tiempo

    return tiempo_ultimo_spawn


def generar_items(items, obstaculos, tiempo, tiempo_ultimo_item_spawn, nivel, jugador_rect):
    COOLDOWN_FRAMES = 140
    if tiempo - tiempo_ultimo_item_spawn < COOLDOWN_FRAMES:
        return tiempo_ultimo_item_spawn
    base_prob = 0.02
    prob = base_prob * (1.0 + 0.02 * max(0, nivel - 1))
    if random.random() >= prob:
        return tiempo_ultimo_item_spawn
    for _ in range(6):
        nuevo = Item()
        # <-- evita que aparezca 'reduccion' si el nivel es 1
        if nuevo.tipo == "reduccion" and nivel <= 1:
            continue
        nuevo.rect.y = jugador_rect.centery - nuevo.rect.height // 2
        nuevo.rect.x = ANCHO + random.randint(20, 260)
        if not any(nuevo.rect.colliderect(o.rect) for o in obstaculos):
            items.append(nuevo)
            return tiempo
    return tiempo_ultimo_item_spawn

def elegir_efecto_misterioso(estado):
    """
    Devuelve un efecto elegido para la caja misteriosa respetando los pesos.
    No devuelve 'reduccion' si el nivel actual es 1.
    """
    opciones = ["escudo", "reduccion", "invulnerable", "subir", "desvalijado"]
    pesos =    [25,       20,          15,           10,       5]
    # Si estamos en nivel 1, eliminamos 'reduccion' (índice 1)
    if estado.get("nivel", 1) <= 1:
        opciones = ["escudo", "invulnerable", "subir", "desvalijado"]
        pesos =    [25,       15,           10,       5]
    return random.choices(opciones, weights=pesos, k=1)[0]


def aplicar_poder_inmediato(tipo, estado):
    ahora = pygame.time.get_ticks()
    if tipo == "escudo":
        estado["escudo"] = True
    elif tipo == "reduccion":
        if estado["nivel"] > 1:
            estado["nivel"] -= 1
            estado["velocidad"] /= 1.25
            estado["mostrar_reduccion"] = True
            estado["tiempo_reduccion"] = ahora + 1000
    elif tipo == "invulnerable":
        estado["invulnerable"] = True
        estado["tiempo_invulnerable"] = ahora + 10000
        estado["color_invul"] = (255, 215, 0)
    elif tipo == "subir":
        estado["nivel"] += 1
        estado["velocidad"] *= 1.25
        estado["mostrar_subida"] = True
        estado["tiempo_subida"] = ahora + 1000
    elif tipo == "desvalijado":
        estado["stack"].clear()
        estado["mostrar_desvalijado"] = True
        estado["tiempo_desvalijado"] = ahora + 1000


def main():
    global ANIM_BY_CHAR

    # crear ventana antes de cargar imágenes
    ventana = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Skater Survival")
    clock = pygame.time.Clock()

    # Cargar background layers (después de set_mode)
    bg_layers = []
    for idx, fname in enumerate(BG_FILES):
        path = os.path.join(BG_DIR, fname)
        if os.path.isfile(path):
            try:
                surf = pygame.image.load(path).convert_alpha()
                w, h = surf.get_size()
                # escalar la capa para que cubra al menos ANCHO x ALTO (manteniendo proporción)
                if w == 0 or h == 0:
                    raise ValueError("background con tamaño inválido")
                scale = max(ANCHO / w, ALTO / h)
                w_s = max(1, int(w * scale))
                h_s = max(1, int(h * scale))
                surf_scaled = pygame.transform.smoothscale(surf, (w_s, h_s))
                layer = {
                    "surf": surf,
                    "surf_scaled": surf_scaled,
                    "w": w,
                    "h": h,
                    "w_scaled": w_s,
                    "h_scaled": h_s,
                    "offset": 0.0,
                    "factor": BG_FACTORS[idx] if idx < len(BG_FACTORS) else 0.5
                }
                bg_layers.append(layer)
            except Exception as e:
                print(f"[WARN] no se pudo cargar background '{path}': {e}")
                bg_layers.append(None)
        else:
            print(f"[WARN] background missing: {path}")
            bg_layers.append(None)

    # cargar sheets por personaje
    ANIM_BY_CHAR = {}
    for char, sheets in CHAR_SHEETS.items():
        ANIM_BY_CHAR[char] = {}
        for key, fname in sheets.items():
            ruta = os.path.join(SPRITE_DIR, fname)
            try:
                surf = pygame.image.load(ruta).convert_alpha()
                # fps: run/roll más rápido
                fps = 12 if key in ("run", "roll") else 8
                ANIM_BY_CHAR[char][key] = AnimatedSprite(surf, fps=fps)
            except Exception as e:
                print(f"[WARN] no se pudo cargar '{fname}' para '{char}': {e}")
                ANIM_BY_CHAR[char][key] = None

    # diagnóstico
    print("DEBUG: working dir:", os.path.abspath(os.getcwd()))
    print("DEBUG: sprite dir exists?", os.path.isdir(SPRITE_DIR))
    print("DEBUG: ANIM_BY_CHAR loaded:", {c: {k: bool(v) for k, v in d.items()} for c, d in ANIM_BY_CHAR.items()})
    print("DEBUG: sheet files requested:", CHAR_SHEETS)

    record_tiempo = 0
    record_nivel = 0

    fuente_tuto = pygame.font.SysFont(None, 26)
    fuente = pygame.font.SysFont(None, 30)

    mostrar_tutorial(ventana, fuente_tuto, fuente, record_tiempo, record_nivel)

    # Selección entre personajes (retorna nombre y anim dict / surface)
    nombre_aspecto, sprite_aspecto = elegir_personaje_multiple(ventana, fuente)
    print("DEBUG: selección final ->", nombre_aspecto, "animaciones cargadas?", isinstance(sprite_aspecto, dict))

    jugador = Player()
    # si sprite_aspecto es dict de AnimatedSprite lo usamos; si es Surface (fallback) lo asignamos
    jugador.set_sprite(sprite_aspecto, SCALE_BY_CHAR.get(nombre_aspecto, 1.8))

    jugador.set_color(FALLBACK_COLORS.get("Azul", (95, 95, 220)))
    jugador.aspecto_nombre = nombre_aspecto

    obstaculos = []
    items = []

    tiempo = 0
    tiempo_ultimo_spawn = 0
    tiempo_ultimo_item_spawn = -9999

    estado = {
        "velocidad": 15.0,
        "nivel": 1,
        "escudo": False,
        "invulnerable": False,
        "tiempo_invulnerable": 0,
        "mostrar_reduccion": False,
        "tiempo_reduccion": 0,
        "mostrar_subida": False,
        "tiempo_subida": 0,
        "mostrar_desvalijado": False,
        "tiempo_desvalijado": 0,
        "stack": [],
        "revelando": False,
        "efecto_revelado": None,
        "tiempo_revelacion": 0,
        "slot_anim_frame": 0,
        "slot_anim_last": 0,
        "color_invul": (255, 215, 0),
        "contador_stack": 0,
        "tiempo_contador": 0
    }

    ultimo_incremento = pygame.time.get_ticks()
    frame_count = 0
    game_over = False

    tiempo_inicio_ms = pygame.time.get_ticks()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()

        if game_over:
            segundos_surv = frame_count // 30
            dibujar_game_over(ventana, fuente, segundos_surv, estado["nivel"], record_tiempo, record_nivel)
            pygame.display.flip()

            if keys[pygame.K_r]:
                jugador = Player()
                jugador.set_sprite(sprite_aspecto, SCALE_BY_CHAR.get(nombre_aspecto, 1.8))

                jugador.set_color(FALLBACK_COLORS.get("Azul", (95, 95, 220)))
                jugador.aspecto_nombre = nombre_aspecto
                obstaculos = []
                items = []
                tiempo = 0
                tiempo_ultimo_spawn = 0
                tiempo_ultimo_item_spawn = -9999
                estado = {
                    "velocidad": 15.0,
                    "nivel": 1,
                    "escudo": False,
                    "invulnerable": False,
                    "tiempo_invulnerable": 0,
                    "mostrar_reduccion": False,
                    "tiempo_reduccion": 0,
                    "mostrar_subida": False,
                    "tiempo_subida": 0,
                    "mostrar_desvalijado": False,
                    "tiempo_desvalijado": 0,
                    "stack": [],
                    "revelando": False,
                    "efecto_revelado": None,
                    "tiempo_revelacion": 0,
                    "slot_anim_frame": 0,
                    "slot_anim_last": 0,
                    "color_invul": (255,215,0),
                    "contador_stack": 0,
                    "tiempo_contador": 0
                }
                ultimo_incremento = pygame.time.get_ticks()
                frame_count = 0
                game_over = False
                tiempo_inicio_ms = pygame.time.get_ticks()
                clock.tick(10)
                continue

            if keys[pygame.K_t]:
                mostrar_tutorial(ventana, fuente_tuto, fuente, record_tiempo, record_nivel)
                nombre_aspecto, sprite_aspecto = elegir_personaje_multiple(ventana, fuente)
                jugador.set_sprite(sprite_aspecto, SCALE_BY_CHAR.get(nombre_aspecto, 1.8))

                jugador.set_color(FALLBACK_COLORS.get("Azul", (95, 95, 220)))
                jugador.aspecto_nombre = nombre_aspecto
                obstaculos = []
                items = []
                tiempo = 0
                tiempo_ultimo_spawn = 0
                tiempo_ultimo_item_spawn = -9999
                estado["stack"].clear()
                ultimo_incremento = pygame.time.get_ticks()
                frame_count = 0
                game_over = False
                tiempo_inicio_ms = pygame.time.get_ticks()
                clock.tick(10)
                continue

            if keys[pygame.K_ESCAPE]:
                pygame.quit()
                sys.exit()

            clock.tick(10)
            continue

        # juego normal
        frame_count += 1
        tiempo += 1
        jugador.manejar_eventos(keys)
        jugador.mover()

        # spawns y demás
        tiempo_ultimo_spawn = generar_obstaculos(obstaculos, tiempo, tiempo_ultimo_spawn)
        tiempo_ultimo_item_spawn = generar_items(items, obstaculos, tiempo, tiempo_ultimo_item_spawn, estado["nivel"], jugador.rect)

        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - ultimo_incremento >= 12000:
            estado["velocidad"] *= 1.25
            estado["nivel"] += 1
            ultimo_incremento = tiempo_actual

        if estado["revelando"]:
            if tiempo_actual - estado["slot_anim_last"] > 100:
                estado["slot_anim_frame"] = (estado["slot_anim_frame"] + 1) % 5
                estado["slot_anim_last"] = tiempo_actual
            if tiempo_actual >= estado["tiempo_revelacion"]:
                aplicar_poder_inmediato(estado["efecto_revelado"], estado)
                estado["revelando"] = False
                estado["efecto_revelado"] = None

        if estado["invulnerable"] and tiempo_actual > estado["tiempo_invulnerable"]:
            estado["invulnerable"] = False
            estado["color_invul"] = (255,215,0)

        for obstaculo in list(obstaculos):
            obstaculo.mover(estado["velocidad"])
            if obstaculo.rect.right < 0:
                obstaculos.remove(obstaculo)
                continue

            hitbox = obstaculo.rect.inflate(-8, -8)
            if jugador.rect.colliderect(hitbox):
                if estado["invulnerable"]:
                    continue
                if estado["escudo"]:
                    estado["escudo"] = False
                    estado["invulnerable"] = True
                    estado["tiempo_invulnerable"] = pygame.time.get_ticks() + 2000
                    estado["color_invul"] = (0,200,255)
                    continue
                if obstaculo.tipo == "techo" and not jugador.agachado:
                    game_over = True
                elif obstaculo.tipo == "suelo" and jugador.rect.bottom > obstaculo.rect.top:
                    game_over = True

        for item in list(items):
            item.mover(estado["velocidad"])
            if item.rect.right < 0:
                items.remove(item)
                continue

            if jugador.rect.colliderect(item.rect):
                tipo = item.tipo
                if tipo == "misterioso":
                    if estado["invulnerable"] or estado["escudo"] or estado["revelando"]:
                        estado["stack"].append(tipo)
                    else:
                        efecto = random.choices(["escudo","reduccion","invulnerable","subir","desvalijado"], weights=[25,20,15,10,5], k=1)[0]
                        estado["revelando"] = True
                        estado["efecto_revelado"] = efecto
                        estado["tiempo_revelacion"] = pygame.time.get_ticks() + 1000
                        estado["slot_anim_frame"] = 0
                        estado["slot_anim_last"] = pygame.time.get_ticks()
                else:
                    if estado["invulnerable"] or estado["escudo"] or estado["revelando"]:
                        estado["stack"].append(tipo)
                    else:
                        aplicar_poder_inmediato(tipo, estado)
                items.remove(item)

        if not estado["invulnerable"] and not estado["escudo"] and not estado["revelando"] and estado["stack"]:
            if estado["contador_stack"] == 0:
                estado["contador_stack"] = 3
                estado["tiempo_contador"] = tiempo_actual + 1000
            else:
                if tiempo_actual >= estado["tiempo_contador"]:
                    estado["contador_stack"] -= 1
                    estado["tiempo_contador"] = tiempo_actual + 1000
                    if estado["contador_stack"] <= 0:
                        siguiente = estado["stack"].pop(0)
                        if siguiente == "misterioso":
                            efecto = random.choices(["escudo","reduccion","invulnerable","subir","desvalijado"], weights=[25,20,15,10,5], k=1)[0]
                            estado["revelando"] = True
                            estado["efecto_revelado"] = efecto
                            estado["tiempo_revelacion"] = pygame.time.get_ticks() + 1000
                            estado["slot_anim_frame"] = 0
                            estado["slot_anim_last"] = pygame.time.get_ticks()
                        else:
                            aplicar_poder_inmediato(siguiente, estado)
                        estado["contador_stack"] = 0
                        estado["tiempo_contador"] = 0

        # DIBUJADO
        ventana.fill(COLOR_FONDO)
        # dibujar background parallax (usa dt = 1 por frame)
        dibujar_background(ventana, bg_layers, estado["velocidad"], 1.0)

        pygame.draw.line(ventana, COLOR_SUELO, (0, ALTO - ALTURA_SUELO), (ANCHO, ALTO - ALTURA_SUELO), 4)
        pygame.draw.line(ventana, COLOR_SUELO, (0, 0), (ANCHO, 0), 4)

        for obstaculo in obstaculos:
            obstaculo.dibujar(ventana)
        for item in items:
            item.dibujar(ventana)

        jugador.dibujar(ventana)

        if estado["invulnerable"]:
            dibujar_icono_poder(ventana, jugador.rect, "INV", estado["color_invul"], inside=True)
        elif estado["escudo"]:
            dibujar_icono_poder(ventana, jugador.rect, "SH", (0,180,255), inside=True)

        if estado["stack"]:
            siguiente = estado["stack"][0]
            label_map = {"escudo":"SH","reduccion":"RD","invulnerable":"IN","misterioso":"?","subir":"UP","desvalijado":"DV"}
            col_map = {"escudo":(0,180,255),"reduccion":(0,255,0),"invulnerable":(255,215,0),"misterioso":(180,0,255),"subir":(255,255,255),"desvalijado":(255,0,0)}
            dibujar_icono_poder(ventana, jugador.rect, label_map.get(siguiente,"?"), col_map.get(siguiente,(200,200,200)),
                                offset_x=- (jugador.rect.width//2 - 30), inside=True)

        if estado["revelando"]:
            center_x = ANCHO // 2
            center_y = ALTO // 2 - 60
            opciones = ["Escudo", "Reducción", "Invulnerable", "Subir nivel", "Desvalijado"]
            col_opts = [(0,180,255),(0,255,0),(255,215,0),(255,255,255),(255,80,80)]
            frame = estado["slot_anim_frame"]
            slot_w, slot_h = 300, 90
            slot_rect = pygame.Rect(center_x - slot_w//2, center_y - slot_h//2, slot_w, slot_h)
            pygame.draw.rect(ventana, (40,40,40), slot_rect)
            pygame.draw.rect(ventana, (200,200,200), slot_rect, 2)
            texto = opciones[frame % len(opciones)]
            color_texto = col_opts[frame % len(col_opts)]
            font_big = pygame.font.SysFont(None, 36)
            surf = font_big.render(texto, True, color_texto)
            ventana.blit(surf, (center_x - surf.get_width()//2, center_y - surf.get_height()//2))

        if estado.get("mostrar_reduccion", False):
            if pygame.time.get_ticks() < estado["tiempo_reduccion"]:
                s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
                s.fill((0,255,0,50))
                ventana.blit(s, (0,0))
                dibujar_texto(ventana, "Nivel abajo", fuente, (0,255,0), (ANCHO//2 - 80, ALTO//2 - 30))
            else:
                estado["mostrar_reduccion"] = False

        if estado.get("mostrar_subida", False):
            if pygame.time.get_ticks() < estado["tiempo_subida"]:
                s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
                s.fill((255,0,0,60))
                ventana.blit(s, (0,0))
                dibujar_texto(ventana, "¡Nivel arriba!", fuente, (255,80,80), (ANCHO//2 - 90, ALTO//2 - 30))
            else:
                estado["mostrar_subida"] = False

        if estado.get("mostrar_desvalijado", False):
            if pygame.time.get_ticks() < estado["tiempo_desvalijado"]:
                s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
                s.fill((255,0,0,80))
                ventana.blit(s, (0,0))
                dibujar_texto(ventana, "¡Desvalijado!", fuente, (255, 120, 120), (ANCHO//2 - 100, ALTO//2 - 10))
            else:
                estado["mostrar_desvalijado"] = False

        segundos_supervivencia = frame_count // 30
        dibujar_texto(ventana, f"Tiempo: {segundos_supervivencia}s", fuente, (255,255,255), (20,20))
        dibujar_texto(ventana, f"Nivel: {estado['nivel']}", fuente, (255,255,0), (20,50))

        record_tiempo = max(record_tiempo, segundos_supervivencia)
        record_nivel = max(record_nivel, estado["nivel"])
        dibujar_texto(ventana, f"Récord tiempo: {record_tiempo}s", fuente, (200,200,200), (20,80))
        dibujar_texto(ventana, f"Récord nivel: {record_nivel}", fuente, (200,200,200), (20,110))

        if estado["escudo"]:
            dibujar_texto(ventana, "ESCUDO", fuente, (0,200,255), (ANCHO - 220, 20))
        if estado["invulnerable"]:
            restante = max(0, (estado["tiempo_invulnerable"] - pygame.time.get_ticks()) // 1000)
            dibujar_texto(ventana, f"INVULNERABLE ({restante}s)", fuente, estado["color_invul"], (ANCHO - 300, 50))
        if estado["stack"]:
            dibujar_texto(ventana, f"Siguiente: {estado['stack'][0].capitalize()}", fuente, (180,0,255), (ANCHO - 280, 80))

        if estado["contador_stack"] > 0:
            dibujar_texto(ventana, f"Activando en {estado['contador_stack']}...", fuente, (255,255,255), (ANCHO//2 - 80, ALTO//2 + 60))

        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    main()
