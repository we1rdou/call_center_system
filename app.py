from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import random
from queue import Queue

# Configuración del servidor Flask
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Variables globales
cola_llamadas = Queue()
llamadas_atendidas = []
lock = threading.Lock()
stop_processing = threading.Event()
pause_processing = threading.Event()
intensive_mode = threading.Event()

# Lista para controlar los hilos
hilos_generadores = []
hilos_atendedores = []

# Número de agentes (configurable)
agentes = 5

# Generación de llamadas aleatorias
def generar_llamada(id_llamada):
    cliente = f"Cliente-{random.randint(1000, 9999)}"
    duracion = random.uniform(0.5, 2)
    return {"id": id_llamada, "cliente": cliente, "duracion": duracion}

# Proceso para generar llamadas
def generador_llamadas():
    i = 1
    while not stop_processing.is_set():
        if pause_processing.is_set():
            time.sleep(0.1)
            continue
        llamada = generar_llamada(i)
        if stop_processing.is_set():
            break
        cola_llamadas.put(llamada)
        print(f"Llamada generada: {llamada}")
        socketio.emit("nueva_llamada", llamada)
        i += 1
        # Modo intensivo: generación rápida de llamadas
        sleep_time = 0.01 if intensive_mode.is_set() else random.uniform(0.05, 0.2)
        time.sleep(sleep_time)

# Proceso para atender llamadas
def procesar_llamada():
    while not stop_processing.is_set():
        if pause_processing.is_set():
            time.sleep(0.1)
            continue
        try:
            llamada = cola_llamadas.get(timeout=0.5)
            if stop_processing.is_set():
                break
            with lock:
                print(f"Atendiendo {llamada['cliente']}...")
                time.sleep(llamada["duracion"])
                llamada["estado"] = "Atendida"
                llamada["atendida_en"] = time.strftime("%Y-%m-%d %H:%M:%S")
                llamadas_atendidas.append(llamada)
                print(f"Llamada atendida: {llamada}")
                socketio.emit("llamada_atendida", llamada)
        except:
            continue

# Iniciar el procesamiento con múltiples agentes
def iniciar_procesamiento():
    stop_processing.clear()
    pause_processing.clear()
    hilos_generadores.clear()
    hilos_atendedores.clear()
    hilo_generador = threading.Thread(target=generador_llamadas, daemon=True)
    hilos_generadores.append(hilo_generador)
    hilo_generador.start()
    for _ in range(agentes):
        hilo = threading.Thread(target=procesar_llamada, daemon=True)
        hilos_atendedores.append(hilo)
        hilo.start()

# Ruta para la página principal
@app.route('/')
def home():
    return render_template('index.html')

# Ruta para pausar el sistema
@app.route('/pausar', methods=['POST'])
def pausar():
    pause_processing.set()
    print("Sistema en pausa")
    return jsonify({"status": "Sistema en pausa"})

# Ruta para reanudar el sistema
@app.route('/reanudar', methods=['POST'])
def reanudar():
    pause_processing.clear()
    print("Sistema reanudado")
    return jsonify({"status": "Sistema reanudado"})

# Ruta para activar el modo intensivo
@app.route('/activar_intensivo', methods=['POST'])
def activar_intensivo():
    intensive_mode.set()
    print("Modo intensivo activado")
    return jsonify({"status": "Modo intensivo activado"})

# Ruta para desactivar el modo intensivo
@app.route('/desactivar_intensivo', methods=['POST'])
def desactivar_intensivo():
    intensive_mode.clear()
    print("Modo intensivo desactivado")
    return jsonify({"status": "Modo intensivo desactivado"})

# Iniciar el procesamiento al iniciar el servidor
iniciar_procesamiento()

# Ejecutar el servidor Flask
if __name__ == '__main__':
    print("Iniciando servidor de Call Center con WebSockets...")
    socketio.run(app, port=5000, debug=True)
    