// Script de diagnóstico para verificar listeners y modales
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== DEBUG MODALS ===');
    
    // Verificar si Bootstrap está cargado
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap no está cargado');
    } else {
        console.log('Bootstrap está cargado');
    }
    
    // Verificar si los modales existen
    const entradaModal = document.getElementById('detallesEntradaModal');
    const salidaModal = document.getElementById('detallesSalidaModal');
    
    console.log('Modal entrada:', entradaModal ? 'EXISTE' : 'NO EXISTE');
    console.log('Modal salida:', salidaModal ? 'EXISTE' : 'NO EXISTE');
    
    // Verificar botones de detalles
    const detalleEntradaBtns = document.querySelectorAll('.btn-detalles-entrada');
    const detalleSalidaBtns = document.querySelectorAll('.btn-detalles-salida');
    const detalleHistorialCompraBtns = document.querySelectorAll('.btn-editar-historial-compra');
    const detalleHistorialVentaBtns = document.querySelectorAll('.btn-editar-historial-venta');
    
    console.log('Botones detalles entrada:', detalleEntradaBtns.length);
    console.log('Botones detalles salida:', detalleSalidaBtns.length);
    console.log('Botones historial compra:', detalleHistorialCompraBtns.length);
    console.log('Botones historial venta:', detalleHistorialVentaBtns.length);
    
    // Agregar listeners de prueba
    detalleEntradaBtns.forEach((btn, index) => {
        btn.addEventListener('click', function(e) {
            console.log('Click en botón detalles entrada #', index);
            e.preventDefault();
            const modal = new bootstrap.Modal(entradaModal);
            modal.show();
        });
    });
    
    detalleSalidaBtns.forEach((btn, index) => {
        btn.addEventListener('click', function(e) {
            console.log('Click en botón detalles salida #', index);
            e.preventDefault();
            const modal = new bootstrap.Modal(salidaModal);
            modal.show();
        });
    });
    
    // Verificar si hay errores en el JS principal
    console.log('FIN DEBUG');
});