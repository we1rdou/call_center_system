from flask import Flask, render_template, jsonify
import threading
import time
import random
from queue import Queue

# Configuración del servidor Flask
app = Flask(__name__)

# Cola de llamadas entrantes
cola_llamadas = Queue()
llamadas_atendidas = []
lock = threading.Lock()

# Número de llamadas a procesar
NUM_LLAMADAS = 50

# Generación de llamadas aleatorias
def generar_llamada(id_llamada):
    cliente = f"Cliente-{random.randint(1000, 9999)}"
    duracion = random.uniform(1, 3)  # Duración de la llamada en segundos
    return {"id": id_llamada, "cliente": cliente, "duracion": duracion}

# Proceso para generar llamadas
def generador_llamadas():
    for i in range(1, NUM_LLAMADAS + 1):
        llamada = generar_llamada(i)
        cola_llamadas.put(llamada)
        print(f"Llamada generada: {llamada}")
        time.sleep(random.uniform(0.1, 0.5))

# Proceso para atender llamadas
def procesar_llamada():
    while not cola_llamadas.empty():
        try:
            llamada = cola_llamadas.get(timeout=1)
            with lock:
                # Simulación de atención de llamada
                print(f"Atendiendo {llamada['cliente']}...")
                time.sleep(llamada["duracion"])
                llamada["estado"] = "Atendida"
                llamada["atendida_en"] = time.strftime("%Y-%m-%d %H:%M:%S")
                llamadas_atendidas.append(llamada)
                print(f"Llamada atendida: {llamada}")
        except:
            continue

# Hilo de procesamiento continuo
def iniciar_procesamiento():
    # Generar llamadas en un hilo separado
    generador_hilo = threading.Thread(target=generador_llamadas)
    generador_hilo.start()

    # Procesar llamadas con múltiples agentes
    hilos = []
    for _ in range(5):  # Cinco agentes atendiendo simultáneamente
        hilo = threading.Thread(target=procesar_llamada)
        hilos.append(hilo)
        hilo.start()

    # Esperar que todos los hilos terminen
    generador_hilo.join()
    for hilo in hilos:
        hilo.join()

# Ruta para la página principal
@app.route('/')
def home():
    return render_template('index.html')

# Ruta para obtener el estado de las llamadas
@app.route('/llamadas', methods=['GET'])
def obtener_llamadas():
    with lock:
        return jsonify({
            "llamadas_atendidas": llamadas_atendidas,  # Mostrar todos los registros atendidos
            "llamadas_pendientes": cola_llamadas.qsize()
        })
# Ruta para reiniciar el sistema
@app.route('/reiniciar', methods=['POST'])
def reiniciar():
    global llamadas_atendidas
    llamadas_atendidas.clear()
    while not cola_llamadas.empty():
        cola_llamadas.get()
    threading.Thread(target=iniciar_procesamiento, daemon=True).start()
    return jsonify({"status": "Sistema reiniciado"})


# Iniciar el procesamiento en un hilo separado
threading.Thread(target=iniciar_procesamiento, daemon=True).start()

# Ejecutar el servidor Flask
if __name__ == '__main__':
    print("Iniciando servidor de Call Center...")
    app.run(port=5000, debug=True, use_reloader=False)
