# 🖐️ Tic-Tac-Toe Vision Control

¡Michi controlado por gestos! Este proyecto utiliza visión artificial para jugar al clásico Tres en Raya (Tic-Tac-Toe) detectando los movimientos y formas de la mano a través de la webcam.

## 🚀 Funcionalidades
* **Control por Gestos:** Olvídate del mouse. El juego reconoce la posición y forma de tu mano.
* **Selección de Ficha:**
    * ✌️ **Signo de la Paz:** Coloca un **Aspa (X)**.
    * ✊ **Puño Cerrado:** Coloca un **Círculo (O)**.
* **Confirmación Inteligente:** Incluye un modo "Hold" para confirmar la jugada solo si mantienes el gesto, evitando errores por movimientos rápidos.
* **Feedback en Pantalla:** Muestra en tiempo real la celda seleccionada, el gesto detectado y el estado de confirmación.

## 🛠️ Tecnologías
* **Python 3.12**
* **OpenCV:** Procesamiento de video y renderizado de la interfaz.
* **Mediapipe:** Seguimiento de puntos de referencia (landmarks) de la mano en tiempo real.
* **NumPy:** Gestión de la lógica del tablero.

## 🕹️ Instrucciones de uso
1. Ejecuta el script principal.
2. Mueve tu mano para desplazarte por la cuadrícula del tablero.
3. Realiza el gesto (Puño o Paz) sobre la celda deseada y mantenlo hasta que el indicador `confirmed` pase a `True`.
4. **Controles de teclado:**
    * `r`: Reiniciar la partida.
    * `q`: Salir del programa.

## 🔧 Instalación

```bash
# Clonar el repositorio
git clone [https://github.com/tu-usuario/nombre-del-repo.git](https://github.com/tu-usuario/nombre-del-repo.git)

# Entrar al directorio
cd nombre-del-repo

# Instalar las librerías necesarias
pip install opencv-python mediapipe numpy
