# Guía de Despliegue del Contrato TrafficStorage

Esta guía te ayudará a desplegar el contrato inteligente `TrafficStorage` en la red BlockDAG (Primordial TestNet).

## Prerrequisitos

1. **Node.js ≥ 18** instalado
2. **Clave privada** de una wallet con fondos en BlockDAG para pagar el gas
3. **Conexión a internet** para acceder al RPC de BlockDAG

## Pasos de Despliegue

### 1. Navegar al directorio de contratos

```bash
cd contracts
```

### 2. Instalar dependencias

Si es la primera vez que trabajas con este proyecto:

```bash
npm install
```

### 3. Configurar la clave privada

Crea un archivo `.env` en el directorio `contracts/` con tu clave privada:

```bash
PRIVATE_KEY=0x_your_private_key_here
```

⚠️ **IMPORTANTE**: 
- Nunca compartas tu clave privada
- Asegúrate de que `.env` esté en `.gitignore`
- Usa una wallet de prueba, no tu wallet principal

### 4. Verificar que tienes fondos

Asegúrate de que la wallet asociada a tu clave privada tenga fondos en BlockDAG. Puedes verificar tu balance en:
- [BlockDAG Explorer](https://bdagscan.com)
- O usando MetaMask conectado a la red BlockDAG (Chain ID: 1043)

### 5. Compilar el contrato

```bash
npx hardhat compile
```

Deberías ver un mensaje de éxito y los archivos compilados en `artifacts/`.

### 6. Desplegar el contrato

```bash
npx hardhat run scripts/deploy.ts --network blockdag
```

El script mostrará:
- La dirección de la cuenta que está desplegando
- El balance de la cuenta
- El progreso del despliegue
- La dirección del contrato desplegado
- El hash de la transacción

### 7. Guardar la dirección del contrato

Después del despliegue exitoso, copia la dirección del contrato que se muestra en la salida.

Ejemplo de salida:
```
✅ DEPLOYMENT SUCCESSFUL!
============================================================
Contract Address: 0x1234567890123456789012345678901234567890
Transaction Hash: 0xabcdef...
```

### 8. Actualizar la configuración del servicio

Edita el archivo `.env` en el directorio raíz de `traffic-storage/` y añade o actualiza:

```bash
BLOCKDAG_CONTRACT_ADDRESS=0x1234567890123456789012345678901234567890
```

Reemplaza `0x1234567890123456789012345678901234567890` con la dirección real de tu contrato.

### 9. Reiniciar el servicio

Si el servicio está corriendo, reinícialo para que cargue la nueva dirección del contrato:

```bash
# Detener el servicio (Ctrl+C)
# Luego iniciarlo de nuevo
./run.sh
```

### 10. Verificar el despliegue

Puedes verificar que el contrato está desplegado correctamente de varias formas:

#### a) Health Check del servicio

```bash
curl http://localhost:8000/healthcheck
```

Deberías ver que `blockdag` está en `true`.

#### b) Explorador de BlockDAG

Visita el explorador y busca tu dirección del contrato:
```
https://bdagscan.com/address/YOUR_CONTRACT_ADDRESS
```

#### c) Verificar código del contrato

El servicio verificará automáticamente que el contrato esté desplegado cuando se inicialice. Si hay problemas, verás mensajes de error en los logs.

## Solución de Problemas

### Error: "insufficient funds"

**Causa**: La wallet no tiene suficientes fondos para pagar el gas.

**Solución**: 
- Asegúrate de tener fondos en BlockDAG en la wallet asociada a tu clave privada
- Puedes obtener fondos de testnet si es necesario

### Error: "nonce too low"

**Causa**: Hay una transacción pendiente o el nonce está desincronizado.

**Solución**: 
- Espera unos segundos y vuelve a intentar
- O espera a que se confirme la transacción anterior

### Error: "network mismatch" o "chain ID mismatch"

**Causa**: La configuración de la red no coincide.

**Solución**: 
- Verifica que `CHAIN_ID=1043` en tu configuración
- Verifica que el RPC URL sea `https://relay.awakening.bdagscan.com/`

### Error: "contract not deployed" después del despliegue

**Causa**: La dirección del contrato no está configurada correctamente o el contrato no se desplegó.

**Solución**:
1. Verifica que copiaste correctamente la dirección del contrato
2. Verifica que actualizaste el `.env` con `BLOCKDAG_CONTRACT_ADDRESS`
3. Verifica en el explorador que el contrato existe en esa dirección
4. Reinicia el servicio después de actualizar el `.env`

### Error: "Could not transact with/call contract function"

**Causa**: El contrato no está desplegado o la dirección es incorrecta.

**Solución**:
1. Verifica que el contrato está desplegado en la dirección especificada
2. Verifica que la dirección en `.env` es correcta (checksum address)
3. Verifica la conectividad con el RPC de BlockDAG

## Comandos Útiles

### Verificar la configuración de Hardhat

```bash
npx hardhat networks
```

### Ejecutar tests del contrato

```bash
npx hardhat test
```

### Limpiar archivos compilados

```bash
npx hardhat clean
```

## Información de la Red BlockDAG

- **Network Name**: BlockDAG Primordial TestNet
- **RPC URL**: https://relay.awakening.bdagscan.com/
- **Chain ID**: 1043
- **Explorer**: https://bdagscan.com
- **Currency**: BDAG

## Notas Importantes

1. **Testnet**: Esta es una red de prueba. No uses fondos reales.
2. **Dirección del contrato**: Una vez desplegado, la dirección del contrato es permanente. Guárdala de forma segura.
3. **Gas**: El despliegue consume gas. Asegúrate de tener fondos suficientes.
4. **Seguridad**: Nunca compartas tu clave privada. Usa variables de entorno y `.gitignore`.

## Siguiente Paso

Una vez desplegado el contrato y configurado el servicio, puedes empezar a usar la API para subir y descargar datos. Consulta el [README principal](../README.md) para más información sobre cómo usar el servicio.


