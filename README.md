# Traffic-Storage: Servicio de Almacenamiento Distribuido

Traffic-Storage es el módulo de almacenamiento del sistema distribuido de gestión de tráfico. Almacena datos vehiculares en IPFS y metadatos en BlockDAG blockchain, proporcionando un sistema de almacenamiento descentralizado y seguro. Expone una API RESTful para subir y descargar datos.

**Nota importante**: Este servicio espera timestamps en formato Unix (int) para compatibilidad con el contrato de BlockDAG. La conversión desde formato ISO se maneja en `traffic-control`.

---

## Estructura del Directorio

```
traffic-storage/
├── api/
│   ├── main.py
│   ├── run_server.py
│   ├── requirements.txt
│   ├── __init__.py
│   ├── config/
│   │   ├── settings.py
│   │   └── logging_config.py
│   ├── models/
│   │   ├── schemas.py
│   │   ├── enums.py
│   │   └── __init__.py
│   ├── services/
│   │   ├── storage_service.py
│   │   ├── ipfs_service.py
│   │   ├── blockdag_service.py
│   │   └── __init__.py
│   ├── api/
│   │   ├── routes/
│   │   │   ├── upload.py
│   │   │   ├── download.py
│   │   │   └── __init__.py
│   │   ├── middleware/
│   │   │   ├── error_handler.py
│   │   │   ├── logging_middleware.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── utils/
│   │   ├── exceptions.py
│   │   ├── validators.py
│   │   └── __init__.py
│   └── storage_manager.py
├── run.sh
├── requirements.txt
├── package.json
├── package-lock.json
├── env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

## Primeros Pasos

### Requisitos previos
* Node.js ≥ 18
* Python ≥ 3.10
* IPFS daemon ejecutándose
* Hardhat configurado para BlockDAG

### Instalar dependencias
```bash
# Dependencias de Node.js
npm install

# Dependencias de Python
pip install -r requirements.txt
```

### Configurar variables de entorno
```bash
cp env.example .env
```
con contenido:
```
# === PINATA IPFS CONFIGURATION ===
PINATA_JWT=your_pinata_jwt_token_here
PINATA_URL=https://your-gateway.mypinata.cloud

# === BLOCKCHAIN CONFIGURATION ===
RPC_URL=https://rpc.primordial.bdagscan.com
PRIVATE_KEY=0x_your_private_key_here
CHAIN_ID=1043
```

### Ejecutar el sistema completo
```
./run.sh
```
Visita: [http://localhost:8000](http://localhost:8000)

---

## API REST

### POST /upload

Sube metadatos de optimización o datos de sensores (formato unificado 2.0). Este endpoint maneja tanto sensores individuales como lotes de múltiples sensores.

**Importante**: Todos los timestamps deben estar en formato Unix (int) para compatibilidad con el contrato de BlockDAG.

**Cuerpo de la solicitud (optimización - formato unificado 2.0):**
```json
{
  "version": "2.0",
  "type": "optimization",
  "timestamp": 1682000000,
  "traffic_light_id": "21",
  "optimizations": [
    {
      "version": "2.0",
      "type": "optimization",
      "timestamp": "2025-05-19T14:20:00Z",
      "traffic_light_id": "21",
      "cluster_sensors": ["21", "22"],
  "optimization": {
        "green_time_sec": 30,
        "red_time_sec": 60
  },
  "impact": {
        "original_congestion": 5,
        "optimized_congestion": 2,
        "original_category": "mild",
        "optimized_category": "none"
      }
  }
  ]
}
```

**Cuerpo de la solicitud (sensor individual - formato unificado 2.0):**
```json
{
  "version": "2.0",
  "type": "data",
  "timestamp": 1682000000,
  "traffic_light_id": "21",
  "sensors": [
    {
      "traffic_light_id": "21",
      "controlled_edges": ["edge42", "edge43"],
      "metrics": {
        "vehicles_per_minute": 65,
        "avg_speed_kmh": 43.5,
        "avg_circulation_time_sec": 92,
        "density": 0.72
      },
      "vehicle_stats": {
        "motorcycle": 12,
        "car": 45,
        "bus": 2,
        "truck": 6
      }
    }
  ]
}
```

**Cuerpo de la solicitud (lote de sensores - formato unificado 2.0):**
```json
{
  "version": "2.0",
  "type": "data",
  "timestamp": 1682000000,
  "traffic_light_id": "21",
  "sensors": [
    {
      "traffic_light_id": "21",
      "controlled_edges": ["edge42", "edge43"],
      "metrics": {
        "vehicles_per_minute": 65,
        "avg_speed_kmh": 43.5,
        "avg_circulation_time_sec": 92,
        "density": 0.72
      },
      "vehicle_stats": {
        "motorcycle": 12,
        "car": 45,
        "bus": 2,
        "truck": 6
      }
    },
    {
      "traffic_light_id": "22",
      "controlled_edges": ["edge44", "edge45"],
      "metrics": {
        "vehicles_per_minute": 78,
        "avg_speed_kmh": 38.2,
        "avg_circulation_time_sec": 105,
        "density": 0.85
      },
      "vehicle_stats": {
        "motorcycle": 8,
        "car": 52,
        "bus": 5,
        "truck": 13
      }
    }
  ]
}
```

**Respuesta (para datos de sensores):**
```json
{
  "message": "Data uploaded successfully",
  "cid": "baf...xyz",
  "type": "data",
  "timestamp": 1682000000,
  "traffic_light_id": "21",
  "sensors_count": 2
}
```

**Respuesta (para optimización):**
```json
{
  "message": "Optimization metadata uploaded successfully",
  "cid": "baf...xyz",
  "type": "optimization",
  "timestamp": 1682000000,
  "traffic_light_id": "21"
}
```

### POST /download

Recupera datos desde IPFS según `traffic_light_id`, `timestamp`, `type`.

**Importante**: El timestamp debe estar en formato Unix (int).

**Cuerpo de la solicitud:**
```json
{
  "traffic_light_id": "21",
  "timestamp": 1682000000,
  "type": "data"
}
```

**Respuesta (formato unificado 2.0):**
```json
{
  "version": "2.0",
  "type": "data",
  "timestamp": 1682000000,
  "traffic_light_id": "21",
  "sensors": [
    {
      "traffic_light_id": "21",
      "controlled_edges": ["edge42", "edge43"],
      "metrics": {
        "vehicles_per_minute": 65,
        "avg_speed_kmh": 43.5,
        "avg_circulation_time_sec": 92,
        "density": 0.72
      },
      "vehicle_stats": {
        "motorcycle": 12,
        "car": 45,
        "bus": 2,
        "truck": 6
      }
    },
    {
      "traffic_light_id": "22",
      "controlled_edges": ["edge44", "edge45"],
      "metrics": {
        "vehicles_per_minute": 78,
        "avg_speed_kmh": 38.2,
        "avg_circulation_time_sec": 105,
        "density": 0.85
      },
      "vehicle_stats": {
        "motorcycle": 8,
        "car": 52,
        "bus": 5,
        "truck": 13
      }
    }
  ]
}
```

### GET /healthcheck

Verifica que el servicio esté activo.

---

## Formato de Datos Unificado 2.0

### Estructura del Lote de Sensores

El formato unificado maneja tanto sensores individuales como lotes de múltiples sensores:

```json
{
  "version": "2.0",
  "type": "data",
  "timestamp": 1682000000,
  "traffic_light_id": "21",
  "sensors": [
    {
      "traffic_light_id": "21",
      "controlled_edges": ["edge42", "edge43"],
      "metrics": {
        "vehicles_per_minute": 65,
        "avg_speed_kmh": 43.5,
        "avg_circulation_time_sec": 92,
        "density": 0.72
      },
      "vehicle_stats": {
        "motorcycle": 12,
        "car": 45,
        "bus": 2,
        "truck": 6
      }
    }
  ]
}
```

### Características del Formato 2.0

- **Versión**: Siempre "2.0" para datos de sensores
- **Tipo**: Siempre "data" para datos de sensores
- **Timestamp**: Timestamp Unix en segundos (int)
- **traffic_light_id**: ID del semáforo de referencia para el lote
- **sensors**: Array de 1 a 10 sensores
  - Cada sensor tiene su propio `traffic_light_id`
  - El `traffic_light_id` de referencia debe estar presente en la lista de sensores

### Validaciones

- **Cantidad de sensores**: Entre 1 y 10 sensores por lote
- **IDs de semáforo**: Solo números (ej: "21", "22")
- **Timestamp**: Formato Unix timestamp (int)
- **Consistencia**: El `traffic_light_id` de referencia debe estar en la lista de sensores

---

## Arquitectura

### IPFS

* Usa `ipfs daemon` para almacenar archivos JSON.
* Soporte para lotes de datos (JSON de JSONs) con múltiples sensores.
* Almacenamiento descentralizado y persistente.

### BlockDAG

* Escribe metadatos en la red Primordial TestNet (`CHAIN_ID=1043`) mediante contratos personalizados.
* Tipo `Data` unificado que maneja tanto sensores individuales como lotes.
* Mapeo: `traffic_light_id => timestamp => DataType => CID`
* **Requiere timestamps Unix** para compatibilidad con el contrato.

### Tipos de Datos Soportados

| Tipo | Valor | Descripción |
|------|-------|-------------|
| `data` | 0 | Datos de sensores |
| `optimization` | 1 | Datos de optimización |

---

## Pruebas

### Pruebas con curl
```bash
# Health check
curl -X GET http://localhost:8000/healthcheck

# Subir sensor individual (formato 2.0 con timestamp Unix)
curl -X POST http://localhost:8000/upload \
  -H "Content-Type: application/json" \
  -d '{
    "version": "2.0",
    "type": "data",
    "timestamp": 1682000000,
    "traffic_light_id": "21",
    "sensors": [
      {
        "traffic_light_id": "21",
        "controlled_edges": ["edge42", "edge43"],
        "metrics": {
          "vehicles_per_minute": 65,
          "avg_speed_kmh": 43.5,
          "avg_circulation_time_sec": 92,
          "density": 0.72
        },
        "vehicle_stats": {
          "motorcycle": 12,
          "car": 45,
          "bus": 2,
          "truck": 6
        }
      }
    ]
  }'

# Subir lote de sensores (formato 2.0 con timestamp Unix)
curl -X POST http://localhost:8000/upload \
  -H "Content-Type: application/json" \
  -d '{
    "version": "2.0",
    "type": "data",
    "timestamp": 1682000000,
    "traffic_light_id": "21",
    "sensors": [
      {
        "traffic_light_id": "21",
        "controlled_edges": ["edge42", "edge43"],
        "metrics": {
          "vehicles_per_minute": 65,
          "avg_speed_kmh": 43.5,
          "avg_circulation_time_sec": 92,
          "density": 0.72
        },
        "vehicle_stats": {
          "motorcycle": 12,
          "car": 45,
          "bus": 2,
          "truck": 6
        }
      },
      {
        "traffic_light_id": "22",
        "controlled_edges": ["edge44", "edge45"],
        "metrics": {
          "vehicles_per_minute": 78,
          "avg_speed_kmh": 38.2,
          "avg_circulation_time_sec": 105,
          "density": 0.85
        },
        "vehicle_stats": {
          "motorcycle": 8,
          "car": 52,
          "bus": 5,
          "truck": 13
        }
      }
    ]
  }'

# Subir datos de optimización (con timestamp Unix)
curl -X POST http://localhost:8000/upload \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0",
    "type": "optimization",
    "timestamp": 1682000000,
    "traffic_light_id": "21",
    "optimization": {
      "signal_timing": [30, 60, 30],
      "cycle_length": 120
    },
    "impact": {
      "avg_wait_time": 45.2,
      "throughput": 0.78
    }
  }'

# Descargar datos (con timestamp Unix)
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{
    "traffic_light_id": "21",
    "timestamp": 1682000000,
    "type": "data"
  }'
```

---

## Compatibilidad

### Funcionalidades Unificadas
- **Un solo endpoint `/upload`**: Maneja tanto sensores individuales como lotes
- **Formato unificado 2.0**: Compatible con 1-10 sensores por lote
- **Retrocompatibilidad**: El formato 2.0 es naturalmente compatible con sensores individuales
- **Respuestas adaptativas**: Incluye `sensors_count` para datos de sensores

### Ventajas del Diseño Unificado
- **Simplicidad**: Un solo endpoint para todos los tipos de datos
- **Consistencia**: Mismo formato para sensores individuales y lotes
- **Escalabilidad**: Fácil extensión para más sensores en el futuro
- **Mantenimiento**: Menos código duplicado y endpoints redundantes

### Manejo de Timestamps
- **Entrada**: Espera timestamps Unix (int) para compatibilidad con BlockDAG
- **Almacenamiento**: Guarda timestamps Unix en el contrato
- **Conversión**: `traffic-control` maneja la conversión desde ISO a Unix
- **Salida**: Devuelve timestamps en el formato original almacenado

---

## Autor
Majo Duarte
