import cv2
import mediapipe as mp
import numpy as np
import time

# -----------------------------
# Config
# -----------------------------
W, H = 640, 480                  # resolución base interna (calidad)
CONFIRM_TIME = 1.0               # mantener gesto 4s para confirmar
WIN_NAME = "Camara | Tic Tac Toe (Resizable)"

# -----------------------------
# MediaPipe Hands
# -----------------------------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# -----------------------------
# Helpers
# -----------------------------
def contar_dedos(hand_landmarks):
    tips = [8, 12, 16, 20]  # índice, medio, anular, meñique
    fingers = 0
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers += 1
    return fingers

def gesto_desde_dedos(dedos):
    if dedos == 0:
        return "FIST"    # puño -> O
    if dedos == 2:
        return "PEACE"   # paz  -> X
    return "OTHER"

def cell_from_point(x, y, grid_origin, grid_wh, n=3):
    ox, oy = grid_origin
    gw, gh = grid_wh
    if x < ox or x >= ox + gw or y < oy or y >= oy + gh:
        return None
    cell_w = gw / n
    cell_h = gh / n
    col = int((x - ox) / cell_w)
    row = int((y - oy) / cell_h)
    return row, col

def check_winner(board):
    lines = []
    lines.extend(board)  # filas
    lines.extend([[board[r][c] for r in range(3)] for c in range(3)])  # columnas
    lines.append([board[i][i] for i in range(3)])  # diag
    lines.append([board[i][2 - i] for i in range(3)])  # diag

    for line in lines:
        if line[0] != "" and line[0] == line[1] == line[2]:
            return line[0]

    if all(board[r][c] != "" for r in range(3) for c in range(3)):
        return "DRAW"
    return None

def draw_grid(img, origin, size, n=3, thickness=3):
    ox, oy = origin
    w, h = size
    cv2.rectangle(img, (ox, oy), (ox + w, oy + h), (255, 255, 255), thickness)
    for i in range(1, n):
        x = int(ox + i * (w / n))
        y = int(oy + i * (h / n))
        cv2.line(img, (x, oy), (x, oy + h), (255, 255, 255), thickness)
        cv2.line(img, (ox, y), (ox + w, y), (255, 255, 255), thickness)

def draw_marks(img, board, origin, size, n=3):
    ox, oy = origin
    w, h = size
    cell_w = w / n
    cell_h = h / n

    for r in range(n):
        for c in range(n):
            mark = board[r][c]
            if mark == "":
                continue

            cx = int(ox + c * cell_w + cell_w / 2)
            cy = int(oy + r * cell_h + cell_h / 2)
            s = int(min(cell_w, cell_h) * 0.28)

            if mark == "O":
                cv2.circle(img, (cx, cy), s, (255, 255, 255), 3)
            elif mark == "X":
                cv2.line(img, (cx - s, cy - s), (cx + s, cy + s), (255, 255, 255), 3)
                cv2.line(img, (cx - s, cy + s), (cx + s, cy - s), (255, 255, 255), 3)

def draw_progress_bar(img, x, y, w, h, progress):
    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), 2)
    fill_w = int(w * max(0.0, min(1.0, progress)))
    cv2.rectangle(img, (x, y), (x + fill_w, y + h), (255, 255, 255), -1)

def get_window_size(name, fallback_w, fallback_h):
    """
    Devuelve (win_w, win_h). En OpenCV moderno (Windows/Linux) suele funcionar.
    Si no está disponible, retorna fallback.
    """
    try:
        # x, y, w, h
        rect = cv2.getWindowImageRect(name)
        return rect[2], rect[3]
    except Exception:
        return fallback_w, fallback_h

# -----------------------------
# Main
# -----------------------------
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)

# tablero
board = [["" for _ in range(3)] for _ in range(3)]
game_over = False
result = None

# confirmación por tiempo (hold 4s) + one-shot
last_gesture = "NONE"
gesture_start_time = None
confirmed = False
stable_cell = None

# tablero grande dentro del canvas
grid_w = 440
grid_h = 440
grid_origin = ((W - grid_w) // 2, (H - grid_h) // 2)
grid_size = (grid_w, grid_h)

# Ventana redimensionable por el usuario
cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WIN_NAME, 1400, 700)  # tamaño inicial cómodo

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (W, H))

    canvas = np.zeros((H, W, 3), dtype=np.uint8)

    # dibuja grilla + marcas
    draw_grid(canvas, grid_origin, grid_size, thickness=4)
    draw_marks(canvas, board, grid_origin, grid_size)

    # mano
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results_mp = hands.process(rgb)

    gesture = "NONE"
    aimed_cell = None

    if results_mp.multi_hand_landmarks:
        hlm = results_mp.multi_hand_landmarks[0]
        mp_drawing.draw_landmarks(frame, hlm, mp_hands.HAND_CONNECTIONS)

        dedos = contar_dedos(hlm)
        gesture = gesto_desde_dedos(dedos)

        x = int(hlm.landmark[8].x * W)
        y = int(hlm.landmark[8].y * H)
        aimed_cell = cell_from_point(x, y, grid_origin, grid_size, n=3)

        # cursor
        cv2.circle(canvas, (x, y), 8, (255, 255, 255), -1)

        # reinicio por cambio de gesto
        if gesture != last_gesture:
            gesture_start_time = time.time()
            confirmed = False
            stable_cell = aimed_cell

        # estabilidad por celda
        if aimed_cell != stable_cell:
            gesture_start_time = time.time()
            confirmed = False
            stable_cell = aimed_cell

        # confirmación por tiempo
        if (not game_over) and (not confirmed) and (gesture in ["FIST", "PEACE"]) and (aimed_cell is not None):
            elapsed = time.time() - gesture_start_time
            progress = min(1.0, elapsed / CONFIRM_TIME)

            cv2.putText(canvas, f"Mantén gesto {CONFIRM_TIME:.0f}s para confirmar",
                        (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            draw_progress_bar(canvas, 10, 140, 240, 18, progress)

            if elapsed >= CONFIRM_TIME:
                r, c = aimed_cell
                if board[r][c] == "":
                    board[r][c] = "O" if gesture == "FIST" else "X"
                    confirmed = True

                    res = check_winner(board)
                    if res is not None:
                        game_over = True
                        result = res

    last_gesture = gesture

    # UI
    cv2.putText(canvas, "MODE: ONE_SHOT + HOLD 4s", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    if aimed_cell is not None:
        cv2.putText(canvas, f"CELDA: {aimed_cell}", (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(canvas, f"GESTO: {gesture} | confirmed: {confirmed}", (10, 85),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    if game_over:
        msg = "EMPATE (DRAW)" if result == "DRAW" else f"GANADOR: {result}"
        cv2.putText(canvas, msg, (10, 175),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 3)

    cv2.putText(canvas, "Controles: r=reiniciar  q=salir", (10, H - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # cámara + canvas lado a lado
    combined = np.hstack([frame, canvas])

    # --- Escalado al tamaño actual de la ventana (lo que pediste) ---
    win_w, win_h = get_window_size(WIN_NAME, combined.shape[1], combined.shape[0])
    if win_w > 50 and win_h > 50:
        combined_view = cv2.resize(combined, (win_w, win_h), interpolation=cv2.INTER_LINEAR)
    else:
        combined_view = combined

    cv2.imshow(WIN_NAME, combined_view)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        board = [["" for _ in range(3)] for _ in range(3)]
        game_over = False
        result = None
        last_gesture = "NONE"
        gesture_start_time = None
        confirmed = False
        stable_cell = None

cap.release()
cv2.destroyAllWindows()
