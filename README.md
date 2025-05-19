# traffic-storage

Módulo de almacenamiento para sistemas de simulación y optimización de tráfico inteligente.

---

## Requisitos previos

* Node.js ≥ 18
* Python ≥ 3.10
* IPFS instalado localmente (`ipfs daemon`)
* Hardhat (vía `npm`)
* Cuenta con fondos en la red Primordial TestNet (`CHAIN_ID=1043`)

---

## Configuración

1. Clona el repositorio:
   ```
   git clone https://github.com/pinv01-25/traffic-storage.git
   ```
2. Crea el archivo `.env` en la raíz usando este ejemplo:
   ```
   cp .env.example .env
   ```
   Contenido del `.env`:
   ```
   BLOCKDAG\_RPC\_URL=https://rpc.primordial.bdagscan.com
   PRIVATE\_KEY=0x43... # Reemplazar con tu clave privada (recomendado usar un burner account)
   CHAIN\_ID=1043
   ```
3. Instala las dependencias:

   ### Backend (API en Python)
   ```
   cd api
   pip install -r requirements.txt
   ```
   ### Smart Contracts (Hardhat + Ethers.js)
   ```
   cd ../contracts
   npm install
   ```
---

## Ejecución local

Este módulo debe estar funcionando **antes** de iniciar `traffic-sim`.

1. Ejecuta todo el sistema con un solo comando:
```
   ./run.sh
```
  Este script:
  
  * Mata cualquier proceso previo en el puerto 8000.
  
  * Lanza el servidor FastAPI en modo desarrollo (uvicorn).
  
  * Inicia automáticamente los servicios necesarios
    
  El servicio quedará disponible en:
  [http://localhost:8000](http://localhost:8000)

---

## Endpoints disponibles

* **POST /upload**
  Sube un objeto tipo `"data"` o `"optimization"` a IPFS y BlockDAG.

* **POST /download**
  Recupera un JSON desde IPFS usando `tls_id`, `timestamp`, `type`.

* **GET /healthcheck**
  Verifica si la API está activa.

