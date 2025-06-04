# Traffic-Storage: Módulo de Almacenamiento Distribuido para Datos de Tráfico

Traffic-Storage es el componente responsable de almacenar datos del sistema de gestión de tráfico inteligente. Guarda información estructurada en IPFS (vía nodo local Kubo) y registra los metadatos en la red BlockDAG (Primordial TestNet). Expone una API RESTful que permite subir y recuperar datos a través de identificadores únicos, tipo y timestamp. También se integra con `traffic-control` y `traffic-sync`.

---

## Estructura del Directorio

```
└── pinv01-25-traffic-storage/
    ├── README.md
    ├── LICENSE
    ├── package.json
    ├── requirements.txt
    ├── run.sh
    ├── vercel.json
    ├── api/
    │   ├── __init__.py
    │   ├── pytest.ini
    │   ├── requirements.txt
    │   ├── server.py
    │   ├── storage_manager.py
    │   ├── modules/
    │   │   ├── blockdag/
    │   │   │   └── blockdag_client.py
    │   │   └── ipfs/
    │   │       └── ipfs_manager.py
    │   ├── scripts/
    │   │   └── generate_jsons.py
    │   └── tests/
    │       ├── test_storage.py
    │       └── input/
    │           ├── invalid_data/
    │           │   └── invalid_data.json
    │           └── valid_data/
    │               └── valid_data.json
    └── contracts/
        ├── hardhat.config.ts
        ├── tsconfig.json
        ├── contracts/
        │   └── TrafficStorage.sol
        ├── scripts/
        │   └── deploy.ts
        └── test/
            └── TrafficStorage.ts

```

---

## Primeros Pasos

### Instalar dependencias

#### API en Python
```
cd api
pip install -r requirements.txt
```
#### Contratos (JS)
```
cd ../contracts
npm install
```
### Crear archivo de entorno
```
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

Sube un objeto JSON a IPFS y registra su hash (CID) en BlockDAG.

**Cuerpo de la solicitud:**
```json
{
  "version": "1.0",
  "type": "data",
  "timestamp": 1682000000,
  "traffic_light_id": "TL-101",
  "controlled_edges": ["E1", "E2"],
  "metrics": {
    "vehicles_per_minute": 35,
    "avg_speed_kmh": 42.7,
    "avg_circulation_time_sec": 30.4,
    "density": 78.9
  },
  "vehicle_stats": {
    "motorcycle": 3,
    "car": 15,
    "bus": 2,
    "truck": 1
  }
}
```
**Respuesta:**
```json
{
"cid": "baf...xyz",
"traffic_light_id": "TL-101",
"timestamp": 1682000000,
"type": "data"
}
```
### POST /download

Recupera un objeto desde IPFS según `traffic_light_id`, `timestamp`, `type`.

**Cuerpo de la solicitud:**
```json
{
"traffic_light_id": "TL-101",
"timestamp": 1682000000,
"type": "data"
}
```
**Respuesta:**
```json
{
  "version": "1.0",
  "type": "data",
  "timestamp": 1682000000,
  "traffic_light_id": "TL-101",
  "controlled_edges": ["E1", "E2"],
  "metrics": {
    "vehicles_per_minute": 35,
    "avg_speed_kmh": 42.7,
    "avg_circulation_time_sec": 30.4,
    "density": 78.9
  },
  "vehicle_stats": {
    "motorcycle": 3,
    "car": 15,
    "bus": 2,
    "truck": 1
  }
}
```
### GET /healthcheck

Verifica que el servicio esté activo.

---

## Arquitectura

### IPFS

* Usa `ipfs daemon` para almacenar archivos JSON.

### BlockDAG

* Escribe metadatos en la red Primordial TestNet (`CHAIN_ID=1043`) mediante contratos personalizados.

---
## Autor
Majo Duarte
