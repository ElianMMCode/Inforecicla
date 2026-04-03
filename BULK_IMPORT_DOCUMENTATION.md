# 📋 Documentación de Bulk Import - Sistema InfoRecicla

## 🚀 Funcionalidad actualizada: Uso de nombres de materiales

El sistema de bulk import ha sido actualizado para usar **nombres de materiales** en lugar de IDs, facilitando la carga masiva de datos y la creación automática de materiales.

## 📁 Formatos CSV Soportados

### 1. Compras de Inventario

**Headers requeridos:**
```
nombreMaterial,cantidad,precioCompra,fechaCompra,observaciones
```

**Ejemplo CSV:**
```csv
nombreMaterial,cantidad,precioCompra,fechaCompra,observaciones
Botellas PET,50.5,1.20,2024-01-15,Botellas plásticas transparentes
Papel Periódico,25.0,0.80,2024-01-16,Papel de periódicos usados
Aluminio Latas,15.3,2.50,2024-01-17,Latas de aluminio compactadas
Cartón Corrugado,100.0,0.60,2024-01-18,Cartón de cajas usadas
Material Nuevo,10.0,1.00,2024-01-19,Material que se creará automáticamente
```

### 2. Ventas de Inventario

**Headers requeridos:**
```
nombreMaterial,cantidad,precioVenta,fechaVenta,centroAcopioId,observaciones
```

**Ejemplo CSV:**
```csv
nombreMaterial,cantidad,precioVenta,fechaVenta,centroAcopioId,observaciones
Botellas PET,30.0,1.50,2024-01-25,1,Venta de botellas procesadas
Papel Periódico,20.0,1.00,2024-01-26,2,Papel clasificado para reproceso
Aluminio Latas,10.0,3.00,2024-01-27,1,Latas limpias y compactadas
```

## ⚙️ Comportamiento del Sistema

### ✅ Materiales Existentes
- Si el material ya existe en el catálogo del punto ECA, se utiliza directamente
- Se busca por nombre (case-insensitive)

### 🆕 Materiales Nuevos
- Si el material no existe, se crea automáticamente con valores por defecto:
  - **Categoría:** "Reciclable"
  - **Tipo:** "Plástico"
  - **Estado:** `es_reciclable=True`, `activo=True`
  - **Inventario:** Se crea con capacidades grandes por defecto

### 📊 Inventario Automático
Cuando se crea un material nuevo, se genera su inventario con:
- `stock_actual=0.0`
- `capacidad_maxima=999999999.0`
- `unidad_medida='KG'`
- `umbral_alerta=80%`
- `umbral_critico=90%`

## 🔧 Endpoints API

### Compras
```
POST /operations/bulk-import-compras/
Content-Type: multipart/form-data
Body: archivo CSV con formato de compras
```

### Ventas
```
POST /operations/bulk-import-ventas/
Content-Type: multipart/form-data
Body: archivo CSV con formato de ventas
```

## 📝 Validaciones

### Campos Obligatorios
- **nombreMaterial:** No puede estar vacío
- **cantidad:** Debe ser un número positivo
- **fecha:** Formato YYYY-MM-DD
- **precio:** Debe ser un número positivo

### Formatos de Fecha Soportados
- `YYYY-MM-DD` (recomendado)
- `DD/MM/YYYY`
- `MM/DD/YYYY`

## 🛡️ Manejo de Errores

El sistema retorna respuestas JSON con:
```json
{
  "status": "success" | "error",
  "mensaje": "Descripción del resultado",
  "errores": ["Lista de errores específicos"],
  "procesados": 15,
  "fallidos": 2
}
```

## 💡 Consejos de Uso

1. **Nombres Consistentes:** Usa nombres consistentes para los materiales
2. **Encoding UTF-8:** Asegúrate de guardar el CSV en UTF-8
3. **Headers Exactos:** Los headers deben coincidir exactamente
4. **Validación Previa:** Revisa centroAcopioId antes de importar ventas
5. **Testing:** Usa archivos pequeños para probar primero

## 🔄 Migración desde IDs

### Antes (inventarioId)
```csv
inventarioId,cantidad,precioCompra,fechaCompra
123,50.5,1.20,2024-01-15
```

### Ahora (nombreMaterial)
```csv
nombreMaterial,cantidad,precioCompra,fechaCompra
Botellas PET,50.5,1.20,2024-01-15
```

## 📈 Ventajas del Nuevo Sistema

- ✅ **Más intuitivo:** No necesitas buscar IDs
- ✅ **Auto-creación:** Los materiales se crean automáticamente
- ✅ **Menos errores:** Reducción de errores de ID inválido
- ✅ **Escalable:** Fácil agregar nuevos materiales
- ✅ **Migración simple:** Cambio mínimo en formato CSV

## 🏷️ Ejemplos Avanzados

### CSV con materiales mixtos (existentes + nuevos)
```csv
nombreMaterial,cantidad,precioCompra,fechaCompra,observaciones
Botellas PET,50.5,1.20,2024-01-15,Material existente
Papel Reciclado Especial,25.0,2.50,2024-01-16,Material nuevo que se creará
Vidrio Transparente,30.0,0.80,2024-01-17,Material existente
Plástico Biodegradable,15.0,3.00,2024-01-18,Innovación que se auto-registra
```

---
*Documentación actualizada para InfoRecicla v2.0 - Sistema de Bulk Import con nombres de materiales*

