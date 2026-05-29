# Tic-Tac-Toe Vision Control — DRON Edition

Michi controlado por gestos usando visión artificial. El video se captura desde un stream RTMP (por ejemplo, la cámara de un dron) y se usa MediaPipe para detectar gestos de la mano en tiempo real.

## Funcionalidades

- **Input RTMP:** Recibe el video desde `rtmp://192.168.137.1/live/key` (cámara del dron u otra fuente RTMP).
- **Reconexión automática:** Si el stream se corta, el programa espera y reconecta sin necesidad de reiniciarlo.
- **Control por gestos:**
  - ✌️ Signo de la paz → coloca **X**
  - ✊ Puño cerrado → coloca **O**
- **Confirmación por tiempo (Hold):** Hay que mantener el gesto sobre la celda durante 1 segundo para confirmar la jugada.
- **Feedback en pantalla:** Celda apuntada, gesto detectado, barra de progreso y estado del juego en tiempo real.

## Tecnologías

- Python 3.12
- OpenCV (con soporte FFmpeg para RTMP)
- MediaPipe 0.10.14
- NumPy

## Instalación

```bash
git clone https://github.com/danieliriartehub/TicTacToe-DRON.git
cd TicTacToe-DRON

pip install opencv-python "mediapipe==0.10.14" numpy
```

## Configuración del stream RTMP

El stream de origen se configura en la variable `RTMP_URL` al inicio del script:

```python
RTMP_URL = "rtmp://192.168.137.1/live/key"
```

Cambia esa URL si tu dron/servidor RTMP usa una dirección diferente.

## Uso

```bash
python TicTacToe_Game.py
```

El programa espera automáticamente a que el stream RTMP esté disponible antes de iniciar.

## Controles de teclado

| Tecla | Acción |
|-------|--------|
| `r`   | Reiniciar partida |
| `q`   | Salir |

## Gestos

| Gesto | Ficha |
|-------|-------|
| ✊ Puño (0 dedos) | O |
| ✌️ Paz (2 dedos) | X |
