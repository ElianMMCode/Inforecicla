/**
 * Script para el Mapa Interactivo de Puntos ECA
 * Responsable de:
 * - Cargar y mostrar puntos ECA en el mapa Leaflet
 * - Sincronizar selecciones entre mapa y lista lateral
 * - Gestionar búsqueda y filtrado de puntos
 * - Manejar popups e información de puntos
 */

class MapaInteractivo {
    constructor() {
        this.mapa = null;
        this.capaMarcadores = null;
        this.marcadores = {};
        this.puntosECA = [];
        this.puntoSeleccionado = null;

        // Coordenadas por defecto (Bogotá, Colombia)
        this.coordenadasDefecto = {
            latitud: 4.7110,
            longitud: -74.0721,
            zoom: 11
        };

        // Colores para marcadores (Bootstrap green - consistente con InfoRecicla)
        this.colores = {
            defecto: '#198754',    // Verde Bootstrap (igual al navbar)
            activo: '#0d6efd',     // Azul Bootstrap
            hover: '#dc3545'       // Rojo Bootstrap
        };

        this.inicializar();
    }

    /**
     * Inicializa la aplicación
     */
    inicializar() {
        console.log('🗺️ Inicializando Mapa Interactivo...');

        // Inicializar mapa
        this.crearMapa();

        // Cargar puntos ECA
        this.cargarPuntosECA();

        // Configurar event listeners
        this.configurarEventos();

        console.log('✅ Mapa Interactivo inicializado');
    }

    /**
     * Crea la instancia del mapa Leaflet
     */
    crearMapa() {
        this.mapa = L.map('mapa', {
            center: [this.coordenadasDefecto.latitud, this.coordenadasDefecto.longitud],
            zoom: this.coordenadasDefecto.zoom,
            attributionControl: true,
            preferCanvas: false
        });

        // Agregar capa de OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19,
            minZoom: 1
        }).addTo(this.mapa);

        // Crear grupo de marcadores con clustering
        this.capaMarcadores = L.markerClusterGroup({
            maxClusterRadius: 80,
            disableClusteringAtZoom: 15
        });
        this.mapa.addLayer(this.capaMarcadores);

        console.log('✅ Mapa Leaflet creado');
    }

    /**
     * Carga los puntos ECA desde el servidor
     */
    cargarPuntosECA() {
        console.log('📍 Cargando puntos ECA...');

        this.mostrarIndicadorCarga(true);

        // URL correcta del endpoint
        fetch('/mapa/api/puntos-eca')
            .then(response => {
                console.log('📡 Response status:', response.status);
                console.log('📡 Response headers:', response.headers);

                if (!response.ok) {
                    throw new Error(`Error HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('📦 JSON recibido:', data);
                console.log(`✅ ${data.length} puntos ECA cargados`);
                this.puntosECA = data;
                this.renderizarMarcadores();
                this.renderizarLista();
                this.actualizarContadores();
            })
            .catch(error => {
                console.error('❌ Error al cargar puntos ECA:', error);
                console.error('Error completo:', error.message);
                this.mostrarError('Error al cargar los puntos ECA. Por favor, intenta más tarde. Error: ' + error.message);
            })
            .finally(() => {
                this.mostrarIndicadorCarga(false);
            });
    }

    /**
     * Renderiza los marcadores en el mapa
     */
    renderizarMarcadores() {
        // Limpiar marcadores existentes
        this.capaMarcadores.clearLayers();
        this.marcadores = {};

        this.puntosECA.forEach(punto => {
            const marcador = this.crearMarcador(punto);
            this.marcadores[punto.puntoEcaID] = marcador;
            this.capaMarcadores.addLayer(marcador);
        });

        // Ajustar vista para mostrar todos los marcadores
        if (Object.keys(this.marcadores).length > 0) {
            this.mapa.fitBounds(this.capaMarcadores.getBounds().pad(0.1));
        }

        console.log('✅ Marcadores renderizados en el mapa');
    }

    /**
     * Crea un marcador individual para un punto ECA
     */
    crearMarcador(punto) {
        // Crear icono personalizado
        const icono = L.divIcon({
            html: `<div class="marcador-custom" style="background-color: ${this.colores.defecto};">
                        <i class="fas fa-leaf"></i>
                   </div>`,
            className: 'marcador-contenedor',
            iconSize: [40, 40],
            iconAnchor: [20, 40],
            popupAnchor: [0, -40]
        });

        // Crear marcador
        const marcador = L.marker(
            [punto.latitud, punto.longitud],
            { icon: icono }
        );

        // Agregar popup
        const contenidoPopup = this.generarContenidoPopup(punto);
        marcador.bindPopup(contenidoPopup, { maxWidth: 300 });

        // Event listeners del marcador
        marcador.on('click', () => {
            this.seleccionarPunto(punto.puntoEcaID);
        });

        marcador.on('mouseover', () => {
            marcador.openPopup();
        });

        // Almacenar referencia al punto en el marcador
        marcador.punto = punto;

        return marcador;
    }

    /**
     * Genera el HTML del contenido del popup
     */
    generarContenidoPopup(punto) {
        return `
            <div class="popup-contenido">
                <div class="popup-titulo">
                    <strong>${this.escaparHTML(punto.nombrePunto)}</strong>
                </div>
                <div class="popup-info">
                    <p class="mb-2">
                        <i class="fas fa-map-pin"></i>
                        <small>${this.escaparHTML(punto.localidadNombre)}</small>
                    </p>
                    ${punto.direccion ? `
                        <p class="mb-2">
                            <i class="fas fa-road"></i>
                            <small>${this.escaparHTML(punto.direccion)}</small>
                        </p>
                    ` : ''}
                    ${punto.celular ? `
                        <p class="mb-2">
                            <i class="fas fa-phone"></i>
                            <small><a href="tel:${punto.celular}">${punto.celular}</a></small>
                        </p>
                    ` : ''}
                    ${punto.email ? `
                        <p class="mb-2">
                            <i class="fas fa-envelope"></i>
                            <small><a href="mailto:${punto.email}">${this.escaparHTML(punto.email)}</a></small>
                        </p>
                    ` : ''}
                    ${punto.horarioAtencion ? `
                        <p class="mb-0">
                            <i class="fas fa-clock"></i>
                            <small>${this.escaparHTML(punto.horarioAtencion)}</small>
                        </p>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Renderiza la lista de puntos en el sidebar
     */
    renderizarLista() {
        const contenedorLista = document.getElementById('listaPuntos');

        if (this.puntosECA.length === 0) {
            contenedorLista.innerHTML = `
                <div class="text-center py-5">
                    <p class="text-muted">
                        <i class="fas fa-info-circle"></i>
                        No hay puntos ECA disponibles
                    </p>
                </div>
            `;
            return;
        }

        let html = '<div class="lista-puntos">';

        this.puntosECA.forEach(punto => {
            html += `
                <div class="tarjeta-punto" data-punto-id="${punto.puntoEcaID}">
                    <div class="tarjeta-titulo">
                        <h6 class="mb-1">${this.escaparHTML(punto.nombrePunto)}</h6>
                        ${punto.localidadNombre ? `
                            <small class="text-muted">${this.escaparHTML(punto.localidadNombre)}</small>
                        ` : ''}
                    </div>
                    
                    <div class="tarjeta-detalles">
                        ${punto.direccion ? `
                            <small>
                                <i class="fas fa-road"></i> ${this.escaparHTML(punto.direccion)}
                            </small>
                        ` : ''}
                        
                        ${punto.celular ? `
                            <small>
                                <i class="fas fa-phone"></i> 
                                <a href="tel:${punto.celular}">${punto.celular}</a>
                            </small>
                        ` : ''}
                        
                        ${punto.email ? `
                            <small>
                                <i class="fas fa-envelope"></i>
                                <a href="mailto:${punto.email}">${this.escaparHTML(punto.email)}</a>
                            </small>
                        ` : ''}
                        
                        ${punto.horarioAtencion ? `
                            <small>
                                <i class="fas fa-clock"></i> ${this.escaparHTML(punto.horarioAtencion)}
                            </small>
                        ` : ''}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        contenedorLista.innerHTML = html;

        // Agregar event listeners a las tarjetas
        document.querySelectorAll('.tarjeta-punto').forEach(tarjeta => {
            tarjeta.addEventListener('click', (e) => {
                const puntoId = tarjeta.dataset.puntoId;
                this.seleccionarPunto(puntoId);
            });
        });

        console.log('✅ Lista de puntos renderizada');
    }

    /**
     * Selecciona un punto y sincroniza mapa y lista
     */
    seleccionarPunto(puntoId) {
        console.log(`🎯 Seleccionando punto: ${puntoId}`);

        // Desmarcar punto anterior
        if (this.puntoSeleccionado) {
            const tarjetaAnterior = document.querySelector(
                `.tarjeta-punto[data-punto-id="${this.puntoSeleccionado}"]`
            );
            if (tarjetaAnterior) {
                tarjetaAnterior.classList.remove('activo');
            }
        }

        // Marcar nuevo punto
        this.puntoSeleccionado = puntoId;
        const tarjeta = document.querySelector(`.tarjeta-punto[data-punto-id="${puntoId}"]`);
        if (tarjeta) {
            tarjeta.classList.add('activo');
            tarjeta.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        // Actualizar marcador en mapa
        const marcador = this.marcadores[puntoId];
        if (marcador) {
            // Cambiar color del marcador
            const icono = L.divIcon({
                html: `<div class="marcador-custom" style="background-color: ${this.colores.activo};">
                            <i class="fas fa-leaf"></i>
                       </div>`,
                className: 'marcador-contenedor',
                iconSize: [40, 40],
                iconAnchor: [20, 40],
                popupAnchor: [0, -40]
            });
            marcador.setIcon(icono);

            // Centrar mapa en el marcador
            this.mapa.setView(marcador.getLatLng(), 14, { animate: true });

            // Abrir popup
            marcador.openPopup();
        }

        // Cargar y mostrar detalles en modal
        this.cargarDetallesPunto(puntoId);
    }

    /**
     * Carga los detalles completos del punto incluyendo materiales
     */
    cargarDetallesPunto(puntoId) {
        console.log(`📊 Cargando detalles del punto: ${puntoId}`);

        fetch(`/mapa/api/puntos-eca/detalle/${puntoId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(detalles => {
                console.log('✅ Detalles cargados:', detalles);
                this.mostrarModalDetalles(detalles);
            })
            .catch(error => {
                console.error('❌ Error al cargar detalles:', error);
                alert('Error al cargar los detalles del punto ECA');
            });
    }

    /**
     * Muestra el modal con los detalles del punto
     */
    mostrarModalDetalles(detalles) {
        // Llenar información general
        document.getElementById('detalleNombre').textContent = detalles.nombrePunto || '';
        document.getElementById('detalleLocalidad').textContent = detalles.localidadNombre || 'No especificada';
        document.getElementById('detalleDireccion').textContent = detalles.direccion || 'No especificada';
        document.getElementById('detalleDescripcion').textContent = detalles.descripcion || 'Sin descripción';

        // Teléfono
        const telLink = document.getElementById('detalleTelefono');
        if (detalles.telefonoPunto) {
            telLink.href = `tel:${detalles.telefonoPunto}`;
            telLink.textContent = detalles.telefonoPunto;
        } else if (detalles.celular) {
            telLink.href = `tel:${detalles.celular}`;
            telLink.textContent = detalles.celular;
        } else {
            telLink.textContent = 'No disponible';
        }

        // Email
        const emailLink = document.getElementById('detalleEmail');
        if (detalles.email) {
            emailLink.href = `mailto:${detalles.email}`;
            emailLink.textContent = detalles.email;
        } else {
            emailLink.textContent = 'No disponible';
        }

        // Horario
        document.getElementById('detalleHorario').textContent = detalles.horarioAtencion || 'No especificado';

        // Llenar tabla de materiales
        this.llenarTablaMateriales(detalles.materiales);

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('modalDetallesPunto'));
        modal.show();
    }

    /**
     * Llena la tabla de materiales en el modal
     */
    llenarTablaMateriales(materiales) {
        const container = document.getElementById('materialesContainer');
        const sinMaterialesMsg = document.getElementById('sinMaterialesMsg');

        if (!materiales || materiales.length === 0) {
            container.innerHTML = '';
            sinMaterialesMsg.style.display = 'block';
            return;
        }

        sinMaterialesMsg.style.display = 'none';

        let html = `
            <table class="table table-sm table-hover">
                <thead class="table-light">
                    <tr>
                        <th><i class="fas fa-box text-success"></i> Material</th>
                        <th><i class="fas fa-layer-group text-success"></i> Tipo</th>
                        <th class="text-end"><i class="fas fa-chart-pie text-success"></i> Capacidad</th>
                        <th class="text-end"><i class="fas fa-dollar-sign text-success"></i> Precio Compra</th>
                    </tr>
                </thead>
                <tbody>
        `;

        materiales.forEach(material => {
            const porcentaje = material.porcentajeCapacidad.toFixed(1);
            const colorBarra = porcentaje > 80 ? 'danger' : (porcentaje > 50 ? 'warning' : 'success');

            html += `
                <tr>
                    <td>
                        <small>
                            <strong>${this.escaparHTML(material.nombreMaterial)}</strong><br>
                            <span class="text-muted">${this.escaparHTML(material.categoriaMaterial)}</span>
                        </small>
                    </td>
                    <td>
                        <small class="badge bg-light text-dark">${this.escaparHTML(material.tipoMaterial)}</small>
                    </td>
                    <td class="text-end">
                        <div class="d-flex align-items-center justify-content-end gap-2">
                            <div class="progress flex-grow-1" style="width: 100px; height: 20px;">
                                <div class="progress-bar bg-${colorBarra}" style="width: ${Math.min(porcentaje, 100)}%"></div>
                            </div>
                            <small class="text-nowrap">${material.stockActual.toFixed(2)} / ${material.capacidadMaxima.toFixed(2)} ${this.escaparHTML(material.unidadMedida)}</small>
                        </div>
                        <small class="text-muted d-block">${porcentaje}%</small>
                    </td>
                    <td class="text-end">
                        <strong class="text-success">$${material.precioBuyPrice.toFixed(2)}</strong>
                    </td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        container.innerHTML = html;
    }

    /**
     * Realiza la búsqueda de puntos
     */
    buscar(termino) {
        console.log(`🔎 Buscando: "${termino}"`);

        const contenedorLista = document.getElementById('listaPuntos');

        if (!termino.trim()) {
            this.renderizarLista();
            return;
        }

        const terminoLower = termino.toLowerCase();
        const puntosFiltrados = this.puntosECA.filter(p =>
            p.nombrePunto.toLowerCase().includes(terminoLower) ||
            (p.localidadNombre && p.localidadNombre.toLowerCase().includes(terminoLower)) ||
            (p.direccion && p.direccion.toLowerCase().includes(terminoLower))
        );

        console.log(`✅ Se encontraron ${puntosFiltrados.length} resultados`);

        if (puntosFiltrados.length === 0) {
            contenedorLista.innerHTML = `
                <div class="text-center py-5">
                    <p class="text-muted">
                        <i class="fas fa-search"></i>
                        No se encontraron resultados
                    </p>
                </div>
            `;
            document.getElementById('contadorActual').textContent = '0';
            return;
        }

        let html = '<div class="lista-puntos">';

        puntosFiltrados.forEach(punto => {
            html += `
                <div class="tarjeta-punto" data-punto-id="${punto.puntoEcaID}">
                    <div class="tarjeta-titulo">
                        <h6 class="mb-1">${this.escaparHTML(punto.nombrePunto)}</h6>
                        ${punto.localidadNombre ? `
                            <small class="text-muted">${this.escaparHTML(punto.localidadNombre)}</small>
                        ` : ''}
                    </div>

                    <div class="tarjeta-detalles">
                        ${punto.direccion ? `
                            <small>
                                <i class="fas fa-road"></i> ${this.escaparHTML(punto.direccion)}
                            </small>
                        ` : ''}

                        ${punto.celular ? `
                            <small>
                                <i class="fas fa-phone"></i> 
                                <a href="tel:${punto.celular}">${punto.celular}</a>
                            </small>
                        ` : ''}

                        ${punto.email ? `
                            <small>
                                <i class="fas fa-envelope"></i>
                                <a href="mailto:${punto.email}">${this.escaparHTML(punto.email)}</a>
                            </small>
                        ` : ''}

                        ${punto.horarioAtencion ? `
                            <small>
                                <i class="fas fa-clock"></i> ${this.escaparHTML(punto.horarioAtencion)}
                            </small>
                        ` : ''}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        contenedorLista.innerHTML = html;

        // Agregar event listeners
        document.querySelectorAll('.tarjeta-punto').forEach(tarjeta => {
            tarjeta.addEventListener('click', () => {
                const puntoId = tarjeta.dataset.puntoId;
                this.seleccionarPunto(puntoId);
            });
        });

        document.getElementById('contadorActual').textContent = puntosFiltrados.length;
    }

    /**
     * Configura los event listeners
     */
    configurarEventos() {
        // Búsqueda por nombre
        const inputBusquedaNombre = document.getElementById('inputBusquedaNombre');
        inputBusquedaNombre.addEventListener('input', (e) => {
            this.aplicarFiltros();
        });

        // Inicializar Select2 para materiales
        const selectMaterial = document.getElementById('selectMaterial');
        $(selectMaterial).select2({
            placeholder: 'Seleccionar material...',
            allowClear: true,
            width: '100%',
            language: 'es'
        });

        // Cargar materiales en Select2
        this.cargarMaterialesEnSelect2();

        // Event listener para cambio en Select2
        $(selectMaterial).on('change', () => {
            this.aplicarFiltros();
        });

        // Botón limpiar filtros
        document.getElementById('btnLimpiarFiltros').addEventListener('click', () => {
            inputBusquedaNombre.value = '';
            $(selectMaterial).val(null).trigger('change');
            this.renderizarLista();
            this.centrarMapa();
        });

        // Botón Centrar
        document.getElementById('btnCentrar').addEventListener('click', () => {
            this.centrarMapa();
        });

        // Botón Recargar
        document.getElementById('btnRecargar').addEventListener('click', () => {
            inputBusquedaNombre.value = '';
            $(selectMaterial).val(null).trigger('change');
            this.cargarPuntosECA();
        });

        // Botones para mobile (mostrar/ocultar lista)
        const btnToggleLista = document.getElementById('btnToggleLista');
        const btnCerrarLista = document.getElementById('btnCerrarLista');
        const sidebarLista = document.getElementById('sidebarLista');

        if (btnToggleLista) {
            btnToggleLista.addEventListener('click', () => {
                sidebarLista.classList.add('visible');
            });
        }

        if (btnCerrarLista) {
            btnCerrarLista.addEventListener('click', () => {
                sidebarLista.classList.remove('visible');
            });
        }

        console.log('✅ Event listeners configurados');
    }

    /**
     * Carga los materiales disponibles en Select2
     */
    cargarMaterialesEnSelect2() {
        console.log('📦 Cargando materiales para Select2...');

        fetch('/mapa/api/materiales')
            .then(response => {
                if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
                return response.json();
            })
            .then(materiales => {
                console.log(`✅ ${materiales.length} materiales cargados`);

                const selectMaterial = document.getElementById('selectMaterial');
                const opcionesHTML = materiales.map(mat =>
                    `<option value="${mat.materialId}">${mat.nombre} (${mat.puntosCantidad} puntos)</option>`
                ).join('');

                selectMaterial.innerHTML = '<option value="">Seleccionar material...</option>' + opcionesHTML;
                $(selectMaterial).trigger('change');
            })
            .catch(error => {
                console.error('❌ Error al cargar materiales:', error);
            });
    }

    /**
     * Aplica los filtros de búsqueda (nombre y material)
     */
    aplicarFiltros() {
        console.log('🔍 Aplicando filtros...');

        const inputNombre = document.getElementById('inputBusquedaNombre').value.toLowerCase();
        const materialId = document.getElementById('selectMaterial').value;

        if (!materialId) {
            // Si no hay material seleccionado, filtrar solo por nombre
            this.filtrarPorNombre(inputNombre);
        } else {
            // Si hay material seleccionado, obtener puntos que lo contengan
            this.filtrarPorMaterial(materialId, inputNombre);
        }
    }

    /**
     * Filtra puntos solo por nombre
     */
    filtrarPorNombre(termino) {
        console.log(`🔎 Filtrando por nombre: "${termino}"`);

        const contenedorLista = document.getElementById('listaPuntos');

        if (!termino.trim()) {
            this.renderizarLista();
            this.actualizarMarcadores(this.puntosECA);
            return;
        }

        const puntosFiltrados = this.puntosECA.filter(p =>
            p.nombrePunto.toLowerCase().includes(termino) ||
            (p.localidadNombre && p.localidadNombre.toLowerCase().includes(termino)) ||
            (p.direccion && p.direccion.toLowerCase().includes(termino))
        );

        console.log(`✅ Se encontraron ${puntosFiltrados.length} resultados`);

        this.mostrarListaFiltrada(puntosFiltrados);
        this.actualizarMarcadores(puntosFiltrados);
        document.getElementById('contadorActual').textContent = puntosFiltrados.length;
    }

    /**
     * Filtra puntos por material
     */
    filtrarPorMaterial(materialId, terminoNombre) {
        console.log(`📦 Filtrando por material: ${materialId}`);

        fetch(`/mapa/api/puntos-eca/por-material/${materialId}`)
            .then(response => {
                if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
                return response.json();
            })
            .then(puntosConMaterial => {
                console.log(`✅ Se encontraron ${puntosConMaterial.length} puntos con el material`);

                // Filtrar también por nombre si está especificado
                let puntosFiltrados = puntosConMaterial;
                if (terminoNombre.trim()) {
                    puntosFiltrados = puntosConMaterial.filter(p =>
                        p.nombrePunto.toLowerCase().includes(terminoNombre) ||
                        (p.localidadNombre && p.localidadNombre.toLowerCase().includes(terminoNombre))
                    );
                    console.log(`✅ Después de filtrar por nombre: ${puntosFiltrados.length} puntos`);
                }

                this.mostrarListaFiltrada(puntosFiltrados);
                this.actualizarMarcadores(puntosFiltrados);
                document.getElementById('contadorActual').textContent = puntosFiltrados.length;
            })
            .catch(error => {
                console.error('❌ Error al filtrar por material:', error);
            });
    }

    /**
     * Muestra la lista filtrada
     */
    mostrarListaFiltrada(puntos) {
        const contenedorLista = document.getElementById('listaPuntos');

        if (puntos.length === 0) {
            contenedorLista.innerHTML = `
                <div class="text-center py-5">
                    <p class="text-muted">
                        <i class="fas fa-search"></i>
                        No se encontraron resultados
                    </p>
                </div>
            `;
            return;
        }

        let html = '<div class="lista-puntos">';

        puntos.forEach(punto => {
            html += `
                <div class="tarjeta-punto" data-punto-id="${punto.puntoEcaID}">
                    <div class="tarjeta-titulo">
                        <h6 class="mb-1">${this.escaparHTML(punto.nombrePunto)}</h6>
                        ${punto.localidadNombre ? `
                            <small class="text-muted">${this.escaparHTML(punto.localidadNombre)}</small>
                        ` : ''}
                    </div>

                    <div class="tarjeta-detalles">
                        ${punto.direccion ? `
                            <small>
                                <i class="fas fa-road"></i> ${this.escaparHTML(punto.direccion)}
                            </small>
                        ` : ''}

                        ${punto.celular ? `
                            <small>
                                <i class="fas fa-phone"></i> 
                                <a href="tel:${punto.celular}">${punto.celular}</a>
                            </small>
                        ` : ''}

                        ${punto.email ? `
                            <small>
                                <i class="fas fa-envelope"></i>
                                <a href="mailto:${punto.email}">${this.escaparHTML(punto.email)}</a>
                            </small>
                        ` : ''}

                        ${punto.horarioAtencion ? `
                            <small>
                                <i class="fas fa-clock"></i> ${this.escaparHTML(punto.horarioAtencion)}
                            </small>
                        ` : ''}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        contenedorLista.innerHTML = html;

        // Agregar event listeners
        document.querySelectorAll('.tarjeta-punto').forEach(tarjeta => {
            tarjeta.addEventListener('click', () => {
                const puntoId = tarjeta.dataset.puntoId;
                this.seleccionarPunto(puntoId);
            });
        });
    }

    /**
     * Actualiza qué marcadores se muestran en el mapa
     */
    actualizarMarcadores(puntos) {
        // Ocultar todos los marcadores primero
        Object.values(this.marcadores).forEach(marcador => {
            this.mapa.removeLayer(marcador);
        });

        // Mostrar solo los marcadores de los puntos filtrados
        puntos.forEach(punto => {
            const marcador = this.crearMarcador(punto);
            if (marcador) {
                marcador.addTo(this.mapa);
            }
        });

        console.log(`✅ Mapa actualizado con ${puntos.length} marcadores`);
    }

    /**
     * Crea un marcador para un punto (helper)
     */
    crearMarcador(punto) {
        const icono = L.divIcon({
            html: `<div class="marcador-custom" style="background-color: ${this.colores.defecto};">
                        <i class="fas fa-leaf"></i>
                   </div>`,
            className: 'marcador-contenedor',
            iconSize: [40, 40],
            iconAnchor: [20, 40],
            popupAnchor: [0, -40]
        });

        const popup = L.popup()
            .setContent(`
                <strong>${this.escaparHTML(punto.nombrePunto)}</strong><br>
                ${punto.localidadNombre ? `<em>${this.escaparHTML(punto.localidadNombre)}</em><br>` : ''}
                ${punto.direccion ? `<small>${this.escaparHTML(punto.direccion)}</small>` : ''}
            `);

        const marcador = L.marker([punto.latitud, punto.longitud], { icon: icono })
            .bindPopup(popup);

        marcador.on('click', () => {
            this.seleccionarPunto(punto.puntoEcaID);
        });

        this.marcadores[punto.puntoEcaID] = marcador;
        return marcador;
    }

    /**
     * Centra el mapa en Bogotá
     */
    centrarMapa() {
        console.log('📍 Centrando mapa...');
        this.mapa.setView(
            [this.coordenadasDefecto.latitud, this.coordenadasDefecto.longitud],
            this.coordenadasDefecto.zoom,
            { animate: true }
        );
    }

    /**
     * Actualiza los contadores de puntos
     */
    actualizarContadores() {
        document.getElementById('contadorActual').textContent = this.puntosECA.length;
        document.getElementById('contadorTotal').textContent = this.puntosECA.length;
    }

    /**
     * Muestra/oculta el indicador de carga
     */
    mostrarIndicadorCarga(mostrar) {
        const indicador = document.getElementById('indicadorCarga');
        if (mostrar) {
            indicador.classList.remove('d-none');
        } else {
            indicador.classList.add('d-none');
        }
    }

    /**
     * Muestra un mensaje de error
     */
    mostrarError(mensaje) {
        const contenedorLista = document.getElementById('listaPuntos');
        contenedorLista.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-circle"></i> ${mensaje}
            </div>
        `;
    }

    /**
     * Escapa caracteres HTML para evitar XSS
     */
    escaparHTML(texto) {
        if (!texto) return '';
        const div = document.createElement('div');
        div.textContent = texto;
        return div.innerHTML;
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new MapaInteractivo();
});

