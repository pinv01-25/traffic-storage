# Traffic Storage - Integration Tests

Este directorio contiene las pruebas de integración y benchmarks del módulo `traffic-storage`.

## Estructura

```
tests/integration/
├── scripts/           # Scripts de automatización para pruebas
├── logs/             # Logs de ejecución y métricas
└── reports/          # Reportes LaTeX generados
```

## Scripts Disponibles

### `storage_metrics.py`
Script principal para medir métricas de rendimiento del sistema de almacenamiento.

**Uso:**
```bash
python3 scripts/storage_metrics.py --scenario bajo --runs 5 --storage-url http://localhost:8000
```

**Parámetros:**
- `--scenario`: Escenario de tráfico (bajo, medio, alto)
- `--runs`: Número de corridas por escenario
- `--storage-url`: URL del servicio traffic-storage
- `--payload`: Archivo JSON con datos de prueba (opcional)
- `--sleep-between`: Tiempo de espera entre corridas (segundos)

### `verify_storage_precision.py`
Script para verificar la precisión de los datos almacenados y recuperados.

**Uso:**
```bash
python3 scripts/verify_storage_precision.py --scenario alto
```

### `run_all.sh`
Script orquestador que ejecuta todas las pruebas automáticamente.

**Uso:**
```bash
./scripts/run_all.sh --runs 5 --storage-url http://localhost:8000
```

## Logs y Métricas

### Estructura de Logs
```
logs/storage_metrics/
├── storage_metrics.csv      # Métricas consolidadas
├── precision_bajo.csv       # Verificación de precisión - escenario bajo
├── precision_medio.csv      # Verificación de precisión - escenario medio
├── precision_alto.csv       # Verificación de precisión - escenario alto
├── bajo/                    # Logs individuales - escenario bajo
├── medio/                   # Logs individuales - escenario medio
└── alto/                    # Logs individuales - escenario alto
```

### Métricas Recolectadas
- **Tiempo de subida**: Duración de operaciones de almacenamiento en IPFS + BlockDAG
- **Tiempo de descarga**: Duración de operaciones de recuperación
- **Precisión**: Verificación criptográfica de integridad de datos
- **CIDs**: Content Identifiers generados por IPFS
- **Status HTTP**: Códigos de respuesta de las operaciones

## Reportes

### `informe_septiembre.tex`
Reporte LaTeX completo con análisis de resultados, metodología y conclusiones.

**Compilación:**
```bash
cd reports/
pdflatex informe_septiembre.tex
```

## Requisitos

- Python 3.8+
- Servicio traffic-storage ejecutándose
- Credenciales configuradas (PINATA_JWT, BLOCKDAG_PRIVATE_KEY)
- Conexión a internet para IPFS y BlockDAG

## Resultados de Pruebas

### Métricas de Rendimiento (Septiembre 2025)

| Escenario | Corridas | Subida (s) avg±sd | Descarga (s) avg±sd | Precisión (%) |
|-----------|----------|-------------------|---------------------|---------------|
| Bajo      | 5        | 6.725±1.035      | 1.981±0.861        | 100           |
| Medio     | 5        | 6.896±0.963      | 1.750±0.136        | 100           |
| Alto      | 5        | 7.290±0.787      | 1.767±0.174        | 100           |

### Consumo de Gas (BlockDAG)

| Tipo de Datos | Gas Consumido | Costo Estimado (USD) |
|---------------|---------------|----------------------|
| Datos de Tráfico | 36,232 | <0.00002 |
| Optimizaciones | 95,624 | <0.00005 |

## Troubleshooting

### Error: "python: command not found"
```bash
# Usar python3 en lugar de python
python3 scripts/storage_metrics.py --help
```

### Error: "HTTP 307 Temporary Redirect"
```bash
# Asegurar que la URL termine con /
--storage-url http://localhost:8000/
```

### Error: "PINATA_JWT not configured"
```bash
# Verificar variables de entorno en .env
cat .env | grep PINATA_JWT
```
