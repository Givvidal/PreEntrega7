# Pre-entrega 7 — API de Producción y Monitoreo Activo

Sistema de agentes desarrollado en Python para la Pre-entrega 7 de Coderhouse. El proyecto expone una API REST con FastAPI, utiliza Redis como cola y almacenamiento de estados, ejecuta un flujo de agentes con LangGraph, incorpora Human-in-the-Loop (HITL) y utiliza Phoenix para observabilidad.

## Requisitos

* Python **3.12**
* Docker Desktop
* Redis Stack
* Una API Key de Google Gemini
* Entorno virtual Python (`venv`)

> **Importante:** este proyecto fue desarrollado y probado utilizando **Python 3.12** dentro de un entorno virtual `.venv`.
>
> No se recomienda utilizar otra versión de Python para reproducir el proyecto.

## Estructura

```text
PreEntrega7/
├── app/
│   ├── main.py
│   ├── graph.py
│   ├── worker.py
│   ├── observability.py
│   └── ...
├── screenshots/
│   ├── phoenix_langgraph_cost.png
│   ├── phoenix_llm_tokens_cost.png
│   ├── hitl_waiting_approval.png
│   ├── hitl_approved_done.png
│   └── load_test_5_concurrent.png
├── load_test.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 1. Crear el entorno virtual

Desde la carpeta raíz del proyecto:

```powershell
py -3.12 -m venv .venv
```

Activar el entorno virtual en Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

La terminal debería mostrar:

```text
(.venv) PS C:\...\PreEntrega7>
```

Todas las dependencias deben instalarse y ejecutarse utilizando este entorno virtual.

## 2. Instalar dependencias

Con `.venv` activado:

```powershell
pip install -r requirements.txt
```

## 3. Configurar las variables de entorno

Crear un archivo `.env` en la raíz del proyecto tomando como referencia `.env.example`.

Las claves reales deben colocarse únicamente en `.env`.

No se debe subir `.env` al repositorio.

Ejemplo:

```env
GOOGLE_API_KEY=TU_API_KEY
```

Los valores reales dependen de las variables utilizadas por el proyecto y están indicados en `.env.example`.

## 4. Redis

El proyecto utiliza Redis para:

* almacenar el estado de las tareas;
* mantener la cola de trabajos;
* almacenar los checkpoints utilizados por LangGraph.

Se utiliza Redis Stack mediante Docker.

Ejemplo para crear el contenedor:

```powershell
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest
```

Si el contenedor ya existe pero está detenido:

```powershell
docker start redis-stack
```

Redis debe estar disponible en:

```text
redis://localhost:6379
```

## 5. Phoenix

Phoenix se utiliza para observar las ejecuciones de LangGraph y las llamadas al modelo.

La configuración utilizada por el proyecto apunta a:

```text
http://localhost:6006/v1/traces
```

Phoenix debe estar disponible en:

```text
http://localhost:6006
```

Antes de ejecutar la API, iniciar Phoenix si se desea registrar y visualizar las trazas.

## 6. Ejecutar la API

Con Redis funcionando, Phoenix disponible y `.venv` activado:

```powershell
uvicorn app.main:app --reload
```

La API queda disponible en:

```text
http://127.0.0.1:8000
```

La documentación automática de FastAPI está disponible en:

```text
http://127.0.0.1:8000/docs
```

## 7. Crear una tarea

El endpoint principal es:

```text
POST /tasks
```

Recibe una consulta y devuelve inmediatamente un `job_id`.

Ejemplo:

```json
{
  "query": "¿Qué es un motor gráfico?",
  "requires_approval": false
}
```

La API responde con un identificador de tarea:

```json
{
  "job_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "PENDING"
}
```

La tarea se coloca en la cola de Redis y es procesada posteriormente por el worker.

## 8. Consultar el estado de una tarea

Utilizar:

```text
GET /tasks/{job_id}
```

Una tarea puede pasar por estados como:

```text
PENDING
RUNNING
WAITING_APPROVAL
DONE
FAILED
```

Ejemplo:

```text
GET /tasks/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## 9. Human-in-the-Loop (HITL)

Las tareas que requieren aprobación pueden enviarse con:

```json
{
  "query": "Tarea crítica de prueba",
  "requires_approval": true
}
```

El flujo se pausa mediante `interrupt()` de LangGraph y la tarea queda en:

```text
WAITING_APPROVAL
```

La aprobación se realiza mediante:

```text
POST /tasks/{job_id}/approve
```

Después de aprobar, el flujo continúa y la tarea debe finalizar en:

```text
DONE
```

Este mecanismo permite demostrar la pausa de una tarea crítica y su posterior reanudación mediante intervención humana.

## 10. Prueba de carga

El archivo:

```text
load_test.py
```

realiza cinco solicitudes concurrentes a la API utilizando `asyncio` y `httpx`.

Ejecutar:

```powershell
python load_test.py
```

El script muestra:

* `job_id` de cada tarea;
* estado final;
* tiempo de ejecución de cada tarea;
* tiempo total;
* P95 de latencia.

Ejemplo de resultado:

```text
RESULTADOS:
{'job_id': '...', 'status': 'DONE', 'tiempo': 75.34}
{'job_id': '...', 'status': 'DONE', 'tiempo': 67.03}
{'job_id': '...', 'status': 'DONE', 'tiempo': 42.07}
{'job_id': '...', 'status': 'DONE', 'tiempo': 55.39}
{'job_id': '...', 'status': 'DONE', 'tiempo': 27.49}

Tiempo total: 75.34s
P95: 67.03s
```

Las cinco tareas se ejecutan concurrentemente y son procesadas mediante la cola de Redis.

## 11. Observabilidad y costos

Phoenix permite visualizar las ejecuciones de LangGraph y las llamadas realizadas al modelo.

Las trazas permiten observar:

* árbol de ejecución;
* nodos de LangGraph;
* llamadas al modelo;
* duración;
* tokens de entrada;
* tokens de salida;
* tokens totales;
* costo de las llamadas.

Las capturas de evidencia se encuentran en:

```text
screenshots/
```

Entre ellas se incluyen evidencias del árbol completo de ejecución, costos y tokens del modelo, ejecución concurrente y flujo HITL.

## 12. Manejo de errores

Las tareas que producen una excepción durante su procesamiento no deben detener el worker completo.

En esos casos el estado de la tarea se guarda como:

```text
FAILED
```

junto con la información del error.

Esto permite que otras tareas de la cola continúen siendo procesadas.

## 13. Reproducción desde un clon limpio

Para reproducir el proyecto desde cero:

```powershell
git clone <URL_DEL_REPOSITORIO>
cd PreEntrega7
```

Crear Python 3.12:

```powershell
py -3.12 -m venv .venv
```

Activar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar:

```powershell
pip install -r requirements.txt
```

Crear `.env` a partir de `.env.example` y colocar las credenciales correspondientes.

Iniciar Redis Stack y Phoenix.

Finalmente ejecutar:

```powershell
uvicorn app.main:app --reload
```

En otra terminal, con el mismo entorno virtual activado, se puede ejecutar:

```powershell
python load_test.py
```

## Importante para una IA o desarrollador que reproduzca el proyecto

Para evitar errores de compatibilidad:

1. Utilizar **Python 3.12**.
2. Crear y activar un entorno virtual `.venv`.
3. Instalar las dependencias desde `requirements.txt`.
4. No utilizar las credenciales contenidas en otro entorno: crear un `.env` propio.
5. Tener Redis Stack disponible en `localhost:6379`.
6. Tener Phoenix disponible en `localhost:6006` para visualizar las trazas.
7. Ejecutar la API desde la carpeta raíz del proyecto.
8. No eliminar ni modificar el sistema de cola, el worker, el checkpointer de Redis ni el flujo HITL al reproducir las pruebas.
9. `load_test.py` debe ejecutarse con la API ya iniciada.
10. Las capturas de `screenshots/` contienen evidencia de las pruebas realizadas durante el desarrollo.
