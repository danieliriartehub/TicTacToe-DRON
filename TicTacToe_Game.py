import cv2
import mediapipe as mp
import time
import math

# ─── Config ───────────────────────────────────────────────────────────────────
RTMP_URL             = "rtmp://192.168.137.1/live/key"
RTMP_RECONNECT_DELAY = 3.0
WIN_NAME             = "TicTacToe DRON  ·  2 Jugadores"
CONFIRM_TIME         = 1.2       # segundos sosteniendo el puño para confirmar
W, H                 = 640, 480  # resolución interna

# ─── Paleta BGR ───────────────────────────────────────────────────────────────
C_P1    = (  0, 210, 255)   # dorado → J1 (X)
C_P2    = ( 40,  60, 230)   # rojo   → J2 (O)
C_WHITE = (255, 255, 255)
C_LGRAY = (160, 160, 160)
C_DGRAY = ( 50,  50,  50)
C_GREEN = ( 50, 200,  50)

PLAYER_COLOR = {1: C_P1, 2: C_P2}
PLAYER_MARK  = {1: "X",  2: "O"}

# ─── Layout del tablero (centrado, debajo del HUD superior) ───────────────────
GW, GH = 330, 330
GOX    = (W - GW) // 2   # 155
GOY    = 82
CW, CH = GW // 3, GH // 3  # 110 × 110 por celda

# ─── MediaPipe ────────────────────────────────────────────────────────────────
_mph  = mp.solutions.hands
_mpd  = mp.solutions.drawing_utils
detector = _mph.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
)

# ─────────────────────────────────────────────────────────────────────────────
# CAPTURA RTMP
# ─────────────────────────────────────────────────────────────────────────────
def open_cap(src):
    cap = cv2.VideoCapture(src)
    if isinstance(src, str):
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap

def safe_read(cap, src):
    ok, frame = cap.read()
    if ok:
        return cap, frame
    if not isinstance(src, str):
        return cap, None
    print("[RTMP] Señal perdida, reconectando…")
    cap.release()
    while True:
        time.sleep(RTMP_RECONNECT_DELAY)
        cap = open_cap(src)
        ok, frame = cap.read()
        if ok:
            print("[RTMP] Reconectado.")
            return cap, frame
        cap.release()

# ─────────────────────────────────────────────────────────────────────────────
# LÓGICA DEL JUEGO
# ─────────────────────────────────────────────────────────────────────────────
def fingers_up(lm):
    return sum(1 for t in [8, 12, 16, 20]
               if lm.landmark[t].y < lm.landmark[t - 2].y)

def is_fist(lm):
    return fingers_up(lm) <= 1

def cell_at(px, py):
    if not (GOX <= px < GOX + GW and GOY <= py < GOY + GH):
        return None
    return (py - GOY) // CH, (px - GOX) // CW

def check_winner(board):
    lines = (
        [board[r] for r in range(3)] +
        [[board[r][c] for r in range(3)] for c in range(3)] +
        [[board[i][i] for i in range(3)]] +
        [[board[i][2 - i] for i in range(3)]]
    )
    for line in lines:
        if line[0] and line[0] == line[1] == line[2]:
            return line[0]
    return "DRAW" if all(board[r][c] for r in range(3) for c in range(3)) else None

def get_win_cells(board):
    checks = (
        [[(r, c) for c in range(3)] for r in range(3)] +
        [[(r, c) for r in range(3)] for c in range(3)] +
        [[(i, i) for i in range(3)]] +
        [[(i, 2 - i) for i in range(3)]]
    )
    for cells in checks:
        vals = [board[r][c] for r, c in cells]
        if vals[0] and vals[0] == vals[1] == vals[2]:
            return cells
    return []

def new_game():
    return {
        "board":   [[""] * 3 for _ in range(3)],
        "current": 1,
        "over":    False,
        "result":  None,
        "wcells":  [],
    }

def new_pstate():
    return {"gstart": None, "confirmed": False, "scell": None, "last_fist": False}

# ─────────────────────────────────────────────────────────────────────────────
# DIBUJO
# ─────────────────────────────────────────────────────────────────────────────
def _blend(base, overlay, alpha):
    """Blend overlay onto base in-place: base = overlay*alpha + base*(1-alpha)."""
    cv2.addWeighted(overlay, alpha, base, 1 - alpha, 0, base)

def _text_x(img_w, text, font, scale, thick):
    (tw, _), _ = cv2.getTextSize(text, font, scale, thick)
    return (img_w - tw) // 2

def draw_x_mark(img, cx, cy, s, col, th=4):
    cv2.line(img, (cx - s, cy - s), (cx + s, cy + s), col, th, cv2.LINE_AA)
    cv2.line(img, (cx - s, cy + s), (cx + s, cy - s), col, th, cv2.LINE_AA)

def draw_o_mark(img, cx, cy, r, col, th=4):
    cv2.circle(img, (cx, cy), r, col, th, cv2.LINE_AA)

# ── Tablero ──────────────────────────────────────────────────────────────────
def draw_board(img, board, wcells):
    ol = img.copy()

    # Fondo semitransparente dentro del tablero
    cv2.rectangle(ol, (GOX, GOY), (GOX + GW, GOY + GH), (8, 8, 8), -1)
    _blend(img, ol, 0.40)

    # Celdas ganadoras
    if wcells:
        ol = img.copy()
        for r, c in wcells:
            x1, y1 = GOX + c * CW + 3, GOY + r * CH + 3
            cv2.rectangle(ol, (x1, y1), (x1 + CW - 6, y1 + CH - 6), C_GREEN, -1)
        _blend(img, ol, 0.32)

    # Líneas de cuadrícula
    ol = img.copy()
    for i in range(1, 3):
        cv2.line(ol, (GOX + i * CW, GOY), (GOX + i * CW, GOY + GH), C_WHITE, 2, cv2.LINE_AA)
        cv2.line(ol, (GOX, GOY + i * CH), (GOX + GW, GOY + i * CH), C_WHITE, 2, cv2.LINE_AA)
    cv2.rectangle(ol, (GOX, GOY), (GOX + GW, GOY + GH), C_WHITE, 2)

    # Marcas con efecto glow
    for r in range(3):
        for c in range(3):
            m = board[r][c]
            if not m:
                continue
            cx_ = GOX + c * CW + CW // 2
            cy_ = GOY + r * CH + CH // 2
            s   = int(min(CW, CH) * 0.30)
            col  = C_P1 if m == "X" else C_P2
            glow = tuple(v // 3 for v in col)
            if m == "X":
                draw_x_mark(ol, cx_, cy_, s + 5, glow, 10)  # glow exterior
                draw_x_mark(ol, cx_, cy_, s,     col,  4)   # línea sólida
            else:
                draw_o_mark(ol, cx_, cy_, s + 5, glow, 10)
                draw_o_mark(ol, cx_, cy_, s,     col,  4)

    _blend(img, ol, 0.92)

# ── Hover de celda ────────────────────────────────────────────────────────────
def draw_hover(img, cell, color):
    if cell is None:
        return
    r, c = cell
    x1, y1 = GOX + c * CW + 4, GOY + r * CH + 4
    ol = img.copy()
    cv2.rectangle(ol, (x1, y1), (x1 + CW - 8, y1 + CH - 8), color, -1)
    _blend(img, ol, 0.22)

# ── Cursor del jugador ────────────────────────────────────────────────────────
def draw_cursor(img, x, y, player, active, progress=0.0):
    col  = PLAYER_COLOR[player]
    mark = PLAYER_MARK[player]
    if active:
        # Arco de progreso
        if progress > 0.02:
            ang = int(360 * min(1.0, progress))
            cv2.ellipse(img, (x, y), (22, 22), -90, 0, ang, col, 3, cv2.LINE_AA)
        # Anillo exterior
        cv2.circle(img, (x, y), 14, col, 2, cv2.LINE_AA)
        # Símbolo central
        if mark == "X":
            draw_x_mark(img, x, y, 5, col, 2)
        else:
            draw_o_mark(img, x, y, 5, col, 2)
    else:
        # Cursor tenue para jugador inactivo
        cv2.circle(img, (x, y), 5, C_LGRAY, 1, cv2.LINE_AA)

# ── Panel de jugador ──────────────────────────────────────────────────────────
def draw_player_panel(img, x1, y1, x2, y2, player, active, score, hand_ok, t):
    col    = PLAYER_COLOR[player]
    mark   = PLAYER_MARK[player]
    hand   = "MANO DERECHA" if player == 1 else "MANO IZQUIERDA"
    border = col if active else C_DGRAY

    # Fondo
    cv2.rectangle(img, (x1, y1), (x2, y2), (18, 18, 18), -1)

    # Borde (pulsa cuando es el turno activo)
    if active:
        pulse = int(180 + 75 * abs(math.sin(t * 3.0)))
        border = tuple(min(255, int(v * pulse / 255)) for v in col)
    cv2.rectangle(img, (x1, y1), (x2, y2), border, 2 if active else 1)

    # Título "J1 (X)"
    cv2.putText(img, f"JUGADOR {player}  ({mark})",
                (x1 + 10, y1 + 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, col, 2, cv2.LINE_AA)

    # Indicador de mano detectada
    dot_col = col if hand_ok else (80, 80, 80)
    cv2.circle(img, (x1 + 15, y1 + 46), 5, dot_col, -1, cv2.LINE_AA)
    cv2.putText(img, hand,
                (x1 + 26, y1 + 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.36, C_LGRAY, 1, cv2.LINE_AA)

    # Puntos
    cv2.putText(img, f"Puntos: {score}",
                (x1 + 10, y1 + 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, C_LGRAY, 1, cv2.LINE_AA)

    # "TU TURNO" badge
    if active:
        badge = "TU TURNO"
        bx    = x2 - 80
        cv2.rectangle(img, (bx - 2, y1 + 4), (x2 - 6, y1 + 22), col, -1)
        cv2.putText(img, badge, (bx, y1 + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (20, 20, 20), 1, cv2.LINE_AA)

# ── HUD completo ──────────────────────────────────────────────────────────────
def draw_hud(img, game, scores, detected_set, t):
    cp = game["current"]
    ov = game["over"]

    # Paneles de jugadores
    draw_player_panel(img,  4,  4, 192, 78, 1, (cp == 1) and not ov,
                      scores[1], 1 in detected_set, t)
    draw_player_panel(img, 448, 4, 636, 78, 2, (cp == 2) and not ov,
                      scores[2], 2 in detected_set, t)

    # Indicador de turno central
    if not ov:
        col  = PLAYER_COLOR[cp]
        txt  = f"TURNO  J{cp}"
        tx   = _text_x(W, txt, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
        cv2.putText(img, txt, (tx, 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, col, 2, cv2.LINE_AA)
        hint = "Cierra el puño sobre una celda para jugar"
        hx   = _text_x(W, hint, cv2.FONT_HERSHEY_SIMPLEX, 0.36, 1)
        cv2.putText(img, hint, (hx, 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, C_LGRAY, 1, cv2.LINE_AA)

    # Barra inferior
    cv2.rectangle(img, (0, H - 30), (W, H), (14, 14, 14), -1)
    cv2.line(img, (0, H - 30), (W, H - 30), C_DGRAY, 1)
    foot = "[R] Reiniciar    [Q] Salir"
    fx   = _text_x(W, foot, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
    cv2.putText(img, foot, (fx, H - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, C_LGRAY, 1, cv2.LINE_AA)

    # Pantalla de game-over
    if ov:
        ol = img.copy()
        cv2.rectangle(ol, (GOX - 10, GOY - 10),
                      (GOX + GW + 10, GOY + GH + 10), (8, 8, 8), -1)
        _blend(img, ol, 0.68)

        if game["result"] == "DRAW":
            msg, sub, col = "EMPATE", "¡Buen partido a los dos!", C_WHITE
        else:
            p   = 1 if game["result"] == "X" else 2
            msg = f"¡JUGADOR {p}  GANA!"
            sub = f"con las  {game['result']}"
            col = PLAYER_COLOR[p]

        cy_center = GOY + GH // 2

        mx = _text_x(W, msg, cv2.FONT_HERSHEY_DUPLEX, 1.3, 3)
        cv2.putText(img, msg, (mx, cy_center - 8),
                    cv2.FONT_HERSHEY_DUPLEX, 1.3, col, 3, cv2.LINE_AA)

        sx = _text_x(W, sub, cv2.FONT_HERSHEY_SIMPLEX, 0.70, 2)
        cv2.putText(img, sub, (sx, cy_center + 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.70, C_LGRAY, 2, cv2.LINE_AA)

        rx = _text_x(W, "[R] Nueva partida", cv2.FONT_HERSHEY_SIMPLEX, 0.50, 1)
        cv2.putText(img, "[R] Nueva partida", (rx, cy_center + 84),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, C_LGRAY, 1, cv2.LINE_AA)

# ─────────────────────────────────────────────────────────────────────────────
# INICIO
# ─────────────────────────────────────────────────────────────────────────────
print(f"[INFO] Conectando a {RTMP_URL} …")
cap = open_cap(RTMP_URL)
if not cap.isOpened():
    print("[RTMP] Sin señal. Esperando…")
    cap.release()
    while True:
        cap = open_cap(RTMP_URL)
        ok, _ = cap.read()
        if ok:
            cap.release()
            cap = open_cap(RTMP_URL)
            break
        cap.release()
        time.sleep(RTMP_RECONNECT_DELAY)
print("[INFO] Stream listo.")

game   = new_game()
scores = {1: 0, 2: 0}
pstate = {1: new_pstate(), 2: new_pstate()}

cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WIN_NAME, 1280, 960)

# ─────────────────────────────────────────────────────────────────────────────
# LOOP PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
while True:
    cap, frame = safe_read(cap, RTMP_URL)
    if frame is None:
        break

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (W, H))

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    det = detector.process(rgb)

    # ── Parsear manos detectadas {player: landmarks} ──────────────────────────
    hands_detected = {}
    if det.multi_hand_landmarks:
        for lm, hd in zip(det.multi_hand_landmarks, det.multi_handedness):
            label  = hd.classification[0].label   # "Right" → J1, "Left" → J2
            player = 1 if label == "Right" else 2
            if player not in hands_detected:       # tomar solo la primera detección
                hands_detected[player] = lm
            _mpd.draw_landmarks(frame, lm, _mph.HAND_CONNECTIONS)

    # ── Lógica de juego + recolectar datos de render ──────────────────────────
    g   = game
    cp  = g["current"]
    now = time.time()
    cursor_data = []   # (x, y, player, active, progress, hover_cell)

    for player, lm in hands_detected.items():
        ps   = pstate[player]
        x    = int(lm.landmark[8].x * W)
        y    = int(lm.landmark[8].y * H)
        cell = cell_at(x, y)
        fist = is_fist(lm)

        # Reiniciar temporizador si cambia gesto o celda
        if fist != ps["last_fist"] or cell != ps["scell"]:
            ps["gstart"]    = now if fist else None
            ps["confirmed"] = False
            ps["scell"]     = cell
        ps["last_fist"] = fist

        active   = (player == cp) and not g["over"]
        progress = 0.0
        hover    = None

        if active and fist and cell and not ps["confirmed"]:
            elapsed  = now - (ps["gstart"] or now)
            progress = min(1.0, elapsed / CONFIRM_TIME)
            hover    = cell

            if elapsed >= CONFIRM_TIME:
                r, c = cell
                if g["board"][r][c] == "":
                    g["board"][r][c] = PLAYER_MARK[player]
                    ps["confirmed"]  = True
                    winner = check_winner(g["board"])
                    if winner:
                        g["over"]   = True
                        g["result"] = winner
                        g["wcells"] = get_win_cells(g["board"])
                        if winner != "DRAW":
                            scores[player] += 1
                    else:
                        other = 3 - player
                        g["current"] = other
                        pstate[other] = new_pstate()

        cursor_data.append((x, y, player, active, progress, hover))

    # ── Render ────────────────────────────────────────────────────────────────
    t = now  # timestamp para animaciones

    # 1. Tablero semi-transparente sobre el stream
    draw_board(frame, g["board"], g["wcells"])

    # 2. Hover de celda (antes del cursor para que quede debajo)
    for x, y, player, active, progress, hover in cursor_data:
        draw_hover(frame, hover, PLAYER_COLOR[player])

    # 3. Cursores
    for x, y, player, active, progress, hover in cursor_data:
        draw_cursor(frame, x, y, player, active, progress)

    # 4. HUD (encima de todo)
    draw_hud(frame, g, scores, set(hands_detected.keys()), t)

    cv2.imshow(WIN_NAME, frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        game   = new_game()
        pstate = {1: new_pstate(), 2: new_pstate()}

cap.release()
cv2.destroyAllWindows()
