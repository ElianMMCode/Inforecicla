/* ===== DATA — cargada desde json_script tags del template ===== */
const _from = (id) => JSON.parse(document.getElementById(id).textContent);
const puntos = _from('puntos-data');
const usuarios = _from('usuarios-data');
const invData = _from('inv-data');
const historial = _from('historial-data');
const eventos = _from('eventos-data');
const conversaciones = _from('conversaciones-data');

/* msgsPorPunto — derivado de conversaciones */
const msgsPorPunto = puntos.map(p => {
  const convs = conversaciones.filter(c => c.puntoId === p.id);
  return {
    puntoId: p.id,
    total: convs.reduce((s, c) => s + (c.msgs || 0), 0),
    sinResponder: convs.length  // placeholder
  };
});

/* Asegurar tipos compatibles con el mockup (id como numero para comparaciones) */
puntos.forEach(p => { p._id = p.id; p.id = parseInt(p.id, 16) || Math.random() * 1e6; });
invData.forEach(i => { i.puntoId = puntos.find(p => p._id === i.puntoId)?.id || 0; });
historial.forEach(h => { h.puntoId = puntos.find(p => p._id === h.puntoId)?.id || 0; });
eventos.forEach(e => { e.puntoId = puntos.find(p => p._id === e.puntoId)?.id || 0; });
conversaciones.forEach(c => { c.puntoId = puntos.find(p => p._id === c.puntoId)?.id || 0; });

/* ===== HELPERS ===== */
function pctOcupacion(item){return item.cap?Math.round((item.stock/item.cap)*100):0;}
function pctOcupacionPunto(p){
  const items=invData.filter(x=>x.puntoId===p.id);
  if(!items.length)return 0;
  const totalStock=items.reduce((s,x)=>s+x.stock,0);
  const totalCap=items.reduce((s,x)=>s+x.cap,0);
  return totalCap?Math.round((totalStock/totalCap)*100):0;
}
function flujoInPunto(p){return invData.filter(x=>x.puntoId===p.id).reduce((s,x)=>s+(x.comprasKg||0),0);}
function flujoOutPunto(p){return invData.filter(x=>x.puntoId===p.id).reduce((s,x)=>s+(x.ventasKg||0),0);}
function margenPunto(p){
  const items=invData.filter(x=>x.puntoId===p.id);
  const totalCompras=items.reduce((s,x)=>s+(x.comprasKg||0)*x.compra,0);
  const totalVentas=items.reduce((s,x)=>s+(x.ventasKg||0)*x.venta,0);
  return totalCompras?Math.round(((totalVentas-totalCompras)/totalCompras)*100):0;
}

/* ===== CHART DEFAULTS ===== */
if(typeof Chart!=='undefined'){Chart.defaults.font.family="'Segoe UI',Tahoma,sans-serif";Chart.defaults.font.size=11;Chart.defaults.plugins.legend.labels.boxWidth=12;Chart.defaults.plugins.legend.labels.padding=8;}
let charts = {};
let currentPuntoId = null;
function destroyChart(id){if(charts[id]){charts[id].destroy();delete charts[id]}}

/* ===== NAVEGACION ===== */
function volverListado(){
  document.getElementById('vista-listado').style.display='';
  document.getElementById('vista-detalle').style.display='none';
  currentPuntoId=null;
}
function openDetalle(id){
  currentPuntoId=id;
  const p=puntos.find(x=>x.id===id);if(!p)return;
  document.getElementById('vista-listado').style.display='none';
  document.getElementById('vista-detalle').style.display='';
  document.getElementById('detalle-nombre').textContent=p.nombre;
  document.getElementById('detalle-breadcrumb-name').textContent=p.nombre;
  document.getElementById('detalle-direccion').innerHTML='<i class="bi bi-geo-alt me-1"></i>'+p.direccion+', '+p.localidad;
  document.getElementById('detalle-badges').innerHTML=
    '<span class="badge bg-success-subtle text-success"><i class="bi bi-person-fill me-1"></i>'+p.gestor+'</span>'+
    '<span class="badge bg-'+(p.estado==='Activo'?'success':'secondary')+'-subtle text-'+(p.estado==='Activo'?'success':'secondary')+'">'+p.estado+'</span>'+
    '<span class="badge bg-primary-subtle text-primary"><i class="bi bi-geo-alt-fill me-1"></i>'+p.localidad+'</span>';
  document.getElementById('detalle-salud').innerHTML=buildSaludBadge(p.invEstado);

  const items=invData.filter(x=>x.puntoId===id);
  document.getElementById('kpi-stock-total').textContent=pctOcupacionPunto(p)+'%';
  document.getElementById('kpi-materiales').textContent=items.length;
  document.getElementById('kpi-movimientos').textContent=historial.length;
  const flujoTotal=flujoInPunto(p)+flujoOutPunto(p);
  document.getElementById('kpi-salud-pct').textContent=flujoTotal.toLocaleString()+' items';

  document.getElementById('resumen-info').innerHTML=
    '<table class="table table-sm table-borderless mb-0" style="font-size:.8rem"><tbody>'+
    '<tr><td class="text-muted">Direccion</td><td class="fw-semibold">'+p.direccion+'</td></tr>'+
    '<tr><td class="text-muted">Localidad</td><td class="fw-semibold">'+p.localidad+'</td></tr>'+
    '<tr><td class="text-muted">Gestor</td><td class="fw-semibold">'+p.gestor+'</td></tr>'+
    '<tr><td class="text-muted">Capacidad</td><td class="fw-semibold">'+pctOcupacionPunto(p)+'% Ocupacion</td></tr>'+
    '<tr><td class="text-muted">Estado</td><td class="fw-semibold">'+p.estado+'</td></tr>'+
    '</tbody></table>';

  const sorted=items.slice().sort((a,b)=>b.stock-a.stock).slice(0,3);
  document.getElementById('resumen-top3').innerHTML=sorted.map((m,i)=>
    '<div class="rank-item"><span class="rank-num '+(i<3?'rank-'+(i+1):'')+'">'+(i+1)+'</span><div class="flex-grow-1"><div class="fw-semibold" style="font-size:.8rem">'+m.mat+'</div><div class="inv-summary">'+Math.round((m.stock/m.cap)*100)+'% ocupacion</div><div class="stock-bar"><div class="stock-bar-fill" style="width:'+(m.stock/m.cap*100)+'%;background:'+(m.stock/m.cap<.3?'#dc3545':m.stock/m.cap<.5?'#ffc107':'#198754')+'"></div></div></div></div>'
  ).join('');

  document.getElementById('resumen-movimientos').innerHTML='<table class="table table-sm table-hover align-middle mb-0"><thead class="table-light"><tr><th>Fecha</th><th>Tipo</th><th>Material</th><th>Kg</th><th>Valor</th></tr></thead><tbody>'+
    historial.slice(0,5).map(m=>'<tr><td class="text-muted" style="font-size:.75rem">'+m.fecha+'</td><td><span class="mov-tipo '+(m.tipo==='Compra'?'mov-compra':'mov-venta')+'"><i class="bi bi-'+(m.tipo==='Compra'?'arrow-down-circle':'arrow-up-circle')+'"></i> '+m.tipo+'</span></td><td class="fw-semibold" style="font-size:.8rem">'+m.mat+'</td><td style="font-size:.8rem">'+m.kg+'</td><td style="font-size:.8rem">$'+m.valor.toLocaleString()+'</td></tr>').join('')+
    '</tbody></table>';

  const hoy=new Date();
  const sinMov=items.filter(x=>{const d=new Date(x.ultimoMov);return isNaN(d.getTime())?false:(hoy-d)/(1000*86400)>30}).map(x=>
    '<tr><td class="fw-semibold" style="font-size:.8rem">'+x.mat+'</td><td style="font-size:.78rem">Stock: '+x.stock+' u</td><td style="font-size:.78rem" class="text-muted">Ult. mov: '+x.ultimoMov+'</td><td><span class="badge bg-danger-subtle text-danger" style="font-size:.65rem">'+Math.round((hoy-new Date(x.ultimoMov))/(1000*86400))+'d sin mov</span></td></tr>'
  ).join('');
  document.getElementById('resumen-sin-mov').innerHTML=sinMov?
    '<table class="table table-sm table-hover align-middle mb-0"><thead class="table-light"><tr><th>Material</th><th>Stock</th><th>Ult. Mov</th><th>Estado</th></tr></thead><tbody>'+sinMov+'</tbody></table>':
    '<div class="p-3 text-center text-muted small">Todos los materiales tienen movimiento reciente.</div>';

  document.getElementById('resumen-eventos').innerHTML=eventos.filter(e=>!e.es_completado).slice(0,3).map(e=>
    '<div class="event-item event-pendiente"><div class="d-flex justify-content-between"><span class="fw-semibold" style="font-size:.8rem">'+e.titulo+'</span><span class="badge bg-warning-subtle text-warning" style="font-size:.65rem">Pendiente</span></div><div class="inv-summary"><i class="bi bi-calendar me-1"></i>'+e.fecha+'</div></div>'
  ).join('');

  initResumenCharts(p);
}

function initResumenCharts(p){
  if(typeof Chart==='undefined')return;
  destroyChart('resumenTendencia');
  const ctx=document.getElementById('chartResumenTendencia');
  if(!ctx)return;
  charts.resumenTendencia=new Chart(ctx,{type:'line',data:{
    labels:['Lun','Mar','Mie','Jue','Vie','Sab','Dom'],
    datasets:[{label:'% Ocupacion',data:[p.stockTotal-80,p.stockTotal-50,p.stockTotal-30,p.stockTotal-60,p.stockTotal-20,p.stockTotal+10,p.stockTotal],
      borderColor:'#198754',backgroundColor:'rgba(25,135,84,.1)',fill:true,tension:.4,pointRadius:3}]
  },options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:false}}}});
}

/* ===== LISTADO ===== */
function buildSaludBadge(s){return'<span class="salud-badge-sm salud-'+s.toLowerCase()+'"><i class="bi bi-heart-fill"></i> '+s+'</span>';}
function buildInvSummary(p){const pct=pctOcupacionPunto(p);return'<div class="inv-summary"><strong>'+pct+'%</strong> Ocupacion</div><div class="stock-bar"><div class="stock-bar-fill" style="width:'+pct+'%;background:'+(pct<30?'#dc3545':pct<50?'#ffc107':'#198754')+'"></div></div>';}

/* ===== LISTADO - KPIs ALWAYS-ON ===== */
function renderKPIs(pts){
  const kpts=pts||puntos;
  let data=invData.filter(x=>kpts.some(p=>p.id===x.puntoId));

  const ptStats=kpts.map(p=>{
    const items=data.filter(x=>x.puntoId===p.id);
    const ventas=items.reduce((s,x)=>s+(x.ventasKg||0),0);
    const compras=items.reduce((s,x)=>s+(x.comprasKg||0),0);
    const mov=ventas+compras;
    const margenProm=items.length?Math.round(items.reduce((s,x)=>s+(x.venta-x.compra),0)/items.length):0;
    return {...p,mov,ventas,compras,margenProm};
  });

  const avgOcupacion=ptStats.length?Math.round(ptStats.reduce((s,p)=>s+pctOcupacionPunto(p),0)/ptStats.length):0;
  const totalFlujoIn=ptStats.reduce((s,p)=>s+flujoInPunto(p),0);
  const totalFlujoOut=ptStats.reduce((s,p)=>s+flujoOutPunto(p),0);
  const avgMargen=ptStats.length?Math.round(ptStats.reduce((s,p)=>s+margenPunto(p),0)/ptStats.length):0;
  const activos=ptStats.filter(p=>p.estado==='Activo').length;
  const sinResp=msgsPorPunto.filter(m=>kpts.some(p=>p.id===m.puntoId)).reduce((s,m)=>s+m.sinResponder,0);
  const gananciaTotal=ptStats.reduce((s,p)=>{
    const items=data.filter(x=>x.puntoId===p.id);
    return s+items.reduce((ss,x)=>ss+(x.ventasKg||0)*x.venta-(x.comprasKg||0)*x.compra,0);
  },0);
  const capSistema=ptStats.length?Math.round(ptStats.reduce((s,p)=>s+pctOcupacionPunto(p),0)/ptStats.length):0;

  const dOcup=Math.round((Math.random()*10-3));const dFlujoIn=Math.round((Math.random()*20-5));
  const dFlujoOut=Math.round((Math.random()*18-4));const dMargen=Math.round((Math.random()*12-4));
  const dActivos=Math.round((Math.random()*4-1));const dSinResp=Math.round((Math.random()*6-4));
  const dGanancia=Math.round((Math.random()*25-8));const dCap=Math.round((Math.random()*8-3));
  function deltaBadge(v){return v>=0?'<span class="badge bg-success-subtle text-success ms-1" style="font-size:.6rem">\u2191'+v+'%</span>':'<span class="badge bg-danger-subtle text-danger ms-1" style="font-size:.6rem">\u2193'+Math.abs(v)+'%</span>';}

  document.getElementById('panel-kpis').innerHTML=
    '<div class="col-6 col-md-3 fade-in-up" style="cursor:pointer" onclick="goToTab(\'resumen\')"><div class="kpi-card-eca kpi-success p-3"><div class="d-flex align-items-center gap-3"><div class="kpi-icon bg-success-subtle text-success"><i class="bi bi-speedometer2"></i></div><div><div class="kpi-value text-success">'+avgOcupacion+'%'+deltaBadge(dOcup)+'</div><div class="kpi-label text-muted">% Ocupacion</div></div></div></div></div>'+
    '<div class="col-6 col-md-3 fade-in-up" style="cursor:pointer" onclick="goToTab(\'flujos\')"><div class="kpi-card-eca kpi-info p-3"><div class="d-flex align-items-center gap-3"><div class="kpi-icon bg-info-subtle text-info"><i class="bi bi-arrow-down-circle"></i></div><div><div class="kpi-value text-info">'+totalFlujoIn.toLocaleString()+deltaBadge(dFlujoIn)+'</div><div class="kpi-label text-muted">Flujo In Total</div></div></div></div></div>'+
    '<div class="col-6 col-md-3 fade-in-up" style="cursor:pointer" onclick="goToTab(\'flujos\')"><div class="kpi-card-eca kpi-primary p-3"><div class="d-flex align-items-center gap-3"><div class="kpi-icon bg-primary-subtle text-primary"><i class="bi bi-arrow-up-circle"></i></div><div><div class="kpi-value text-primary">'+totalFlujoOut.toLocaleString()+deltaBadge(dFlujoOut)+'</div><div class="kpi-label text-muted">Flujo Out Total</div></div></div></div></div>'+
    '<div class="col-6 col-md-3 fade-in-up" style="cursor:pointer" onclick="goToTab(\'flujos\')"><div class="kpi-card-eca kpi-warning p-3"><div class="d-flex align-items-center gap-3"><div class="kpi-icon bg-warning-subtle text-warning"><i class="bi bi-cash-stack"></i></div><div><div class="kpi-value text-warning">'+avgMargen+'%'+deltaBadge(dMargen)+'</div><div class="kpi-label text-muted">Margen Promedio</div></div></div></div></div>'+
    '<div class="col-6 col-md-3 fade-in-up" style="cursor:pointer" onclick="goToTab(\'flujos\')"><div class="kpi-card-eca kpi-dark p-3"><div class="d-flex align-items-center gap-3"><div class="kpi-icon bg-dark-subtle text-dark"><i class="bi bi-currency-dollar"></i></div><div><div class="kpi-value text-dark">$'+Math.round(gananciaTotal).toLocaleString()+deltaBadge(dGanancia)+'</div><div class="kpi-label text-muted">Ganancia Total</div></div></div></div></div>'+
    '<div class="col-6 col-md-3 fade-in-up" style="cursor:pointer" onclick="goToTab(\'estados\')"><div class="kpi-card-eca kpi-success p-3"><div class="d-flex align-items-center gap-3"><div class="kpi-icon bg-success-subtle text-success"><i class="bi bi-geo-alt-fill"></i></div><div><div class="kpi-value text-success">'+activos+deltaBadge(dActivos)+'</div><div class="kpi-label text-muted">Pts Activos</div></div></div></div></div>'+
    '<div class="col-6 col-md-3 fade-in-up" style="cursor:pointer" onclick="goToTab(\'estados\')"><div class="kpi-card-eca kpi-info p-3"><div class="d-flex align-items-center gap-3"><div class="kpi-icon bg-info-subtle text-info"><i class="bi bi-boxes"></i></div><div><div class="kpi-value text-info">'+capSistema+'%'+deltaBadge(dCap)+'</div><div class="kpi-label text-muted">Capacidad Sistema</div></div></div></div></div>'+
    '<div class="col-6 col-md-3 fade-in-up" style="cursor:pointer" onclick="goToTab(\'mensajes\')"><div class="kpi-card-eca kpi-danger p-3"><div class="d-flex align-items-center gap-3"><div class="kpi-icon bg-danger-subtle text-danger"><i class="bi bi-chat-dots"></i></div><div><div class="kpi-value text-danger">'+sinResp+deltaBadge(dSinResp)+'</div><div class="kpi-label text-muted">Msgs Sin Resp</div></div></div></div></div>';
}

/* ===== HELPER — filtro por tab ===== */
function _fitrarPtsTab(searchId, locId, estadoId){
  if(!searchId)return puntos.slice();
  const search=(document.getElementById(searchId)?.value||'').toLowerCase();
  const locVal=locId?(document.getElementById(locId)?.value||''):'';
  const estVal=estadoId?(document.getElementById(estadoId)?.value||''):'';
  let pts=puntos.slice();
  if(search)pts=pts.filter(p=>p.nombre.toLowerCase().includes(search)||p.direccion.toLowerCase().includes(search));
  if(locVal)pts=pts.filter(p=>p.localidad===locVal);
  if(estVal)pts=pts.filter(p=>p.estado===estVal);
  return pts;
}

/* ===== LISTADO - TABS ===== */
let activeListadoTab='resumen';
let estadosMap=null;
function goToTab(tab){
  const linkMap={resumen:0,estados:1,flujos:2,mensajes:3};
  const links=document.querySelectorAll('#listado-tabs .nav-link');
  if(links[linkMap[tab]])switchListadoTab(tab,links[linkMap[tab]]);
}
function switchListadoTab(tab,el){
  activeListadoTab=tab;
  el.closest('.tab-nav').querySelectorAll('.nav-link').forEach(a=>a.classList.remove('active'));
  el.classList.add('active');
  ['resumen','estados','flujos','mensajes'].forEach(t=>{
    const pane=document.getElementById('tab-listado-'+t);
    if(pane)pane.style.display=(t===tab)?'':'none';
  });
  if(tab==='resumen')renderResumen();
  else if(tab==='estados')renderEstados();
  else if(tab==='flujos'){renderFlujoVolumen();}
  else if(tab==='mensajes')renderMensajesListado();
}

/* ===== LISTADO - RESUMEN ===== */
function renderResumen(){
  const pts=_fitrarPtsTab('res-search-input','res-loc-filter','res-estado-filter');
  let data=invData.slice();

  const resMat=document.getElementById('res-mat-filter')?.value||'';
  const resOrden=document.getElementById('res-orden')?.value||'mov';
  if(resMat)data=data.filter(x=>x.mat===resMat);
  data=data.filter(x=>pts.some(p=>p.id===x.puntoId));

  if(typeof Chart==='undefined'){
    document.getElementById('chartPanelTop').parentElement.innerHTML='<div class="p-4 text-center text-muted"><i class="bi bi-info-circle me-1"></i>Graficas no disponibles — requiere Chart.js CDN</div>';
  } else {
    destroyChart('panelTop');

  /* Chart #1 — Top 10 */
  const top10=[...pts].sort((a,b)=>{
    const fA=flujoInPunto(a)+flujoOutPunto(a);
    const fB=flujoInPunto(b)+flujoOutPunto(b);
    if(resOrden==='mov')return fB-fA;
    if(resOrden==='ventas')return flujoInPunto(b)-flujoInPunto(a);
    if(resOrden==='compras')return flujoOutPunto(b)-flujoOutPunto(a);
    if(resOrden==='margen')return margenPunto(b)-margenPunto(a);
    return fB-fA;
  }).slice(0,10);
  const tLabels=top10.map(p=>p.nombre.substring(0,14));
  const tFlujoIn=top10.map(p=>flujoInPunto(p));
  const tFlujoOut=top10.map(p=>flujoOutPunto(p));
  charts.panelTop=new Chart(document.getElementById('chartPanelTop'),{type:'bar',data:{labels:tLabels,datasets:[
    {label:'Flujo In',data:tFlujoIn,backgroundColor:'#0d6efd',borderRadius:4,barPercentage:.7},
    {label:'Flujo Out',data:tFlujoOut,backgroundColor:'#198754',borderRadius:4,barPercentage:.7}
  ]},options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,title:{display:true,text:'items'}}},plugins:{legend:{position:'bottom'}}}});

  /* Table auxiliar */
  const matTableHtml=top10.map(p=>{
    const items=invData.filter(x=>x.puntoId===p.id);
    const masVendido=items.length?items.slice().sort((a,b)=>(b.ventasKg||0)-(a.ventasKg||0))[0]:null;
    const masComprado=items.length?items.slice().sort((a,b)=>(b.comprasKg||0)-(a.comprasKg||0))[0]:null;
    return'<tr><td class="fw-semibold" style="font-size:.78rem">'+p.nombre.substring(0,16)+'</td>'+
      '<td style="font-size:.75rem">'+(masVendido?masVendido.mat:'-')+'</td>'+
      '<td style="font-size:.75rem">'+(masComprado?masComprado.mat:'-')+'</td></tr>';
  }).join('');
  document.getElementById('res-mat-table').innerHTML='<table class="table table-sm table-hover align-middle mb-0"><thead class="table-light"><tr><th>Punto</th><th>Mas Vendido</th><th>Mas Comprado</th></tr></thead><tbody>'+matTableHtml+'</tbody></table>';
  }

  /* Capacidad General */
  const capTotal=pts.length?pts.reduce((s,p)=>s+pctOcupacionPunto(p),0)/pts.length:0;
  const activosRes=pts.filter(p=>p.estado==='Activo').length;
  const capColor=capTotal<30?'#dc3545':capTotal<50?'#ffc107':'#198754';
  document.getElementById('res-capacidad-general').innerHTML=
    '<div class="text-center"><div style="font-size:2.8rem;font-weight:800;color:'+capColor+'">'+Math.round(capTotal)+'%</div>'+
    '<div style="font-size:.75rem;color:#6c757d;margin-bottom:8px">Ocupacion promedio del sistema</div>'+
    '<div class="progress" style="height:14px;width:100%"><div class="progress-bar" style="width:'+Math.round(capTotal)+'%;background:'+capColor+';border-radius:7px"></div></div>'+
    '<div class="mt-2" style="font-size:.65rem;color:#6c757d">'+pts.length+' puntos — '+activosRes+' activos</div></div>';

  /* Top 3 Materiales */
  if(typeof Chart!=='undefined'){
    const matTrans={};historial.forEach(m=>{matTrans[m.mat]=(matTrans[m.mat]||0)+m.valor});
  const top3Mat=Object.entries(matTrans).sort((a,b)=>b[1]-a[1]).slice(0,3);
  destroyChart('resTopMat');
  const tmCanvas=document.getElementById('chartResTopMat');
  if(tmCanvas){
    charts.resTopMat=new Chart(tmCanvas,{type:'doughnut',data:{labels:top3Mat.map(e=>e[0]),datasets:[{data:top3Mat.map(e=>e[1]),backgroundColor:['#198754','#0d6efd','#ffc107']}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'}}}});
    }
  }

  /* Ultimos Puntos Creados */
  const ultPts=[...pts].sort((a,b)=>new Date(b.fecha_creacion)-new Date(a.fecha_creacion)).slice(0,5);
  document.getElementById('res-ultimos-puntos').innerHTML=
    '<table class="table table-sm table-hover align-middle mb-0"><thead class="table-light"><tr><th>Punto</th><th>Creado</th><th>Estado</th></tr></thead><tbody>'+
    ultPts.map(p=>'<tr style="cursor:pointer" onclick="openDetalle('+p.id+')"><td class="fw-semibold" style="font-size:.78rem">'+p.nombre.substring(0,16)+'</td><td style="font-size:.72rem;color:#6c757d">'+p.fecha_creacion+'</td><td><span class="badge bg-'+(p.estado==='Activo'?'success':'secondary')+'-subtle text-'+(p.estado==='Activo'?'success':'secondary')+'" style="font-size:.65rem">'+p.estado+'</span></td></tr>').join('')+
    '</tbody></table>';

  /* Actividad Temporal */
  if(typeof Chart!=='undefined'){
    const mesesOrden=['Ene','Feb','Mar','Abr','May','Jun'];const mesesData={};
  mesesOrden.forEach(m=>{mesesData[m]={compras:0,ventas:0}});
  historial.forEach(h=>{const m=h.fecha.split('-')[1];const idx=parseInt(m)-1;if(idx>=0&&idx<6){const mn=mesesOrden[idx];mesesData[mn][h.tipo.toLowerCase()]=(mesesData[mn][h.tipo.toLowerCase()]||0)+h.valor;}});
  destroyChart('resActividadTemporal');
  const atCanvas=document.getElementById('chartResActividadTemporal');
  if(atCanvas){
    charts.resActividadTemporal=new Chart(atCanvas,{type:'bar',data:{labels:mesesOrden,datasets:[
      {label:'Compras ($)',data:mesesOrden.map(m=>mesesData[m].compras),backgroundColor:'#0d6efd',borderRadius:4,barPercentage:.7},
      {label:'Ventas ($)',data:mesesOrden.map(m=>mesesData[m].ventas),backgroundColor:'#198754',borderRadius:4,barPercentage:.7}
    ]},options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,title:{display:true,text:'$ COP'}}},plugins:{legend:{position:'bottom'}}}});
  }
  }

  /* Feed Actividad Reciente */
  const feedItems=[];
  historial.slice(0,4).forEach(h=>{
    const p=puntos.find(pt=>pt.id===h.puntoId||pt.mat===h.mat);const pn=p?p.nombre:'';
    feedItems.push({tiempo:h.fecha.substring(5),icono:'bi-arrow-'+(h.tipo==='Compra'?'down':'up')+'-circle',color:h.tipo==='Compra'?'text-primary':'text-success',texto:h.tipo+' de '+h.mat+' ('+h.kg+' u) — '+pn.substring(0,14)});
  });
  conversaciones.slice(0,2).forEach(c=>{
    feedItems.push({tiempo:c.fecha.substring(5,16),icono:'bi-chat-dots',color:'text-warning',texto:c.ciudadano+': '+c.ultimo.substring(0,40)});
  });
  document.getElementById('res-feed-actividad').innerHTML=feedItems.slice(0,6).map(f=>
    '<div class="d-flex align-items-start gap-2 p-2 border-bottom" style="font-size:.72rem">'+
    '<i class="bi '+f.icono+' '+f.color+' mt-1" style="font-size:.85rem"></i>'+
    '<div><div>'+f.texto+'</div><div class="text-muted" style="font-size:.65rem">'+f.tiempo+'</div></div></div>'
  ).join('')||'<div class="p-3 text-muted text-center">Sin actividad reciente</div>';
}

/* ===== LISTADO - RANKING ===== */
let rankingSortCol='mov',rankingSortDir=-1;
let rankingPage=1,rankingPerPage=20;
function sortRanking(col){
  if(rankingSortCol===col)rankingSortDir*=-1;else{rankingSortCol=col;rankingSortDir=-1;}
  rankingPage=1;
  renderRanking();
}
function limpiarFiltrosRanking(){
  document.getElementById('rank-flt-nombre').value='';
  document.getElementById('rank-flt-localidad').value='';
  document.getElementById('rank-flt-estado').value='';
  document.getElementById('rank-flt-salud').value='';
  document.getElementById('rank-flt-ocup-min').value='';
  document.getElementById('rank-flt-ocup-max').value='';
  rankingPage=1;
  renderRanking();
}
function renderRanking(resetPage){
  if(resetPage!==false)rankingPage=1;
  let pts=puntos.slice();
  const col=rankingSortCol,dir=rankingSortDir;

  const fltNombre=(document.getElementById('rank-flt-nombre')?.value||'').toLowerCase();
  const fltLoc=document.getElementById('rank-flt-localidad')?.value||'';
  const fltEstado=document.getElementById('rank-flt-estado')?.value||'';
  const fltSalud=document.getElementById('rank-flt-salud')?.value||'';
  const fltOcupMin=parseInt(document.getElementById('rank-flt-ocup-min')?.value)||0;
  const fltOcupMax=parseInt(document.getElementById('rank-flt-ocup-max')?.value)||100;

  const enriched=pts.map(p=>{
    const flujoIn=flujoInPunto(p);
    const flujoOut=flujoOutPunto(p);
    const ocupacion=pctOcupacionPunto(p);
    const margen=margenPunto(p);
    const sinRespItem=msgsPorPunto.find(m=>m.puntoId===p.id);
    const sinResp=sinRespItem?sinRespItem.sinResponder:0;
    const totalMsgs=sinRespItem?sinRespItem.total:0;
    const items=invData.filter(x=>x.puntoId===p.id);
    const comprasCOP=items.reduce((s,x)=>s+(x.comprasKg||0)*x.compra,0);
    const ventasCOP=items.reduce((s,x)=>s+(x.ventasKg||0)*x.venta,0);
    const ganancia=ventasCOP-comprasCOP;
    const matRentable=items.length?items.slice().sort((a,b)=>{
      const ma=(a.venta-a.compra);const mb=(b.venta-b.compra);
      return mb-ma;
    })[0]:null;
    return {...p,flujoIn,flujoOut,ocupacion,margenProm:margen,sinResp,totalMsgs,comprasCOP,ventasCOP,ganancia,matRentable};
  });

  let filtered=enriched;
  if(fltNombre)filtered=filtered.filter(p=>p.nombre.toLowerCase().includes(fltNombre)||p.direccion.toLowerCase().includes(fltNombre));
  if(fltLoc)filtered=filtered.filter(p=>p.localidad===fltLoc);
  if(fltEstado)filtered=filtered.filter(p=>p.estado===fltEstado);
  if(fltSalud)filtered=filtered.filter(p=>p.invEstado===fltSalud);
  filtered=filtered.filter(p=>p.ocupacion>=fltOcupMin&&p.ocupacion<=fltOcupMax);

  const sorted=[...filtered].sort((a,b)=>{
    let va=a[col]??0, vb=b[col]??0;
    if(col==='flujoIn'){va=a.flujoIn;vb=b.flujoIn;}
    if(col==='flujoOut'){va=a.flujoOut;vb=b.flujoOut;}
    if(col==='ocupacion'){va=a.ocupacion;vb=b.ocupacion;}
    if(col==='margenProm'){va=a.margenProm;vb=b.margenProm;}
    if(col==='sinResp'){va=a.sinResp;vb=b.sinResp;}
    if(col==='totalMsgs'){va=a.totalMsgs;vb=b.totalMsgs;}
    if(col==='comprasCOP'){va=a.comprasCOP;vb=b.comprasCOP;}
    if(col==='ventasCOP'){va=a.ventasCOP;vb=b.ventasCOP;}
    if(col==='ganancia'){va=a.ganancia;vb=b.ganancia;}
    if(col==='nombre')return a.nombre.localeCompare(b.nombre)*dir;
    if(col==='localidad')return a.localidad.localeCompare(b.localidad)*dir;
    if(col==='invEstado')return a.invEstado.localeCompare(b.invEstado)*dir;
    return (va-vb)*dir;
  });

  const headers=[
    {col:'nombre',l:'Punto'},{col:'localidad',l:'Localidad'},{col:'gestor',l:'Gestor'},
    {col:'invEstado',l:'Salud'},{col:'ocupacion',l:'% Ocupacion'},
    {col:'flujoIn',l:'Flujo In'},{col:'flujoOut',l:'Flujo Out'},
    {col:'comprasCOP',l:'Compras $'},{col:'ventasCOP',l:'Ventas $'},
    {col:'ganancia',l:'Ganancia $'},{col:'margenProm',l:'Margen %'},
    {col:'estado',l:'Estado'},{col:'totalMsgs',l:'Msgs'},
    {col:'sinResp',l:'Sin Resp'}
  ];
  const totalCols=headers.length+2;
  document.getElementById('ranking-thead').innerHTML='<tr><th style="width:40px">#</th>'+headers.map(h=>'<th style="cursor:pointer;white-space:nowrap" onclick="sortRanking(\''+h.col+'\')">'+h.l+(h.col===col?(dir===1?' <i class="bi bi-sort-up"></i>':' <i class="bi bi-sort-down"></i>'):'')+'</th>').join('')+'<th class="text-center">Accion</th></tr>';

  /* Paginacion */
  const totalRegistros=sorted.length;
  const totalPaginas=Math.ceil(totalRegistros/rankingPerPage);
  if(rankingPage>totalPaginas)rankingPage=totalPaginas||1;
  const inicio=(rankingPage-1)*rankingPerPage;
  const pagina=sorted.slice(inicio,inicio+rankingPerPage);

  document.getElementById('ranking-tbody').innerHTML=pagina.map((p,i)=>{
    const pctOcu=p.ocupacion;
    const barColor=pctOcu<30?'#dc3545':pctOcu<50?'#ffc107':'#198754';
    return'<tr style="cursor:pointer" onclick="openDetalle('+p.id+')"><td class="fw-bold text-muted">'+(inicio+i+1)+'</td>'+
      '<td class="fw-semibold text-success" style="font-size:.82rem">'+p.nombre+'</td>'+
      '<td style="font-size:.78rem" class="text-muted">'+p.localidad+'</td>'+
      '<td style="font-size:.78rem">'+p.gestor+'</td>'+
      '<td class="text-center">'+buildSaludBadge(p.invEstado)+'</td>'+
      '<td style="font-size:.82rem">'+pctOcu+'%<div class="stock-bar"><div class="stock-bar-fill" style="width:'+pctOcu+'%;background:'+barColor+'"></div></div></td>'+
      '<td style="font-size:.82rem">'+p.flujoIn.toLocaleString()+'</td>'+
      '<td style="font-size:.82rem">'+p.flujoOut.toLocaleString()+'</td>'+
      '<td style="font-size:.82rem">$'+Math.round(p.comprasCOP).toLocaleString()+'</td>'+
      '<td style="font-size:.82rem">$'+Math.round(p.ventasCOP).toLocaleString()+'</td>'+
      '<td style="font-size:.82rem" class="fw-bold '+(p.ganancia>=0?'text-success':'text-danger')+'">$'+Math.round(p.ganancia).toLocaleString()+'</td>'+
      '<td style="font-size:.82rem" class="fw-bold '+(p.margenProm>=0?'text-success':'text-danger')+'">'+p.margenProm+'%</td>'+
      '<td class="text-center"><span class="badge bg-'+(p.estado==='Activo'?'success':'secondary')+'-subtle text-'+(p.estado==='Activo'?'success':'secondary')+' rounded-pill px-3" style="font-size:.72rem">'+p.estado+'</span></td>'+
      '<td class="text-center">'+p.totalMsgs+'</td>'+
      '<td class="text-center">'+(p.sinResp>0?'<span class="badge bg-danger rounded-pill px-2" style="font-size:.72rem">'+p.sinResp+'</span>':'<span class="text-muted" style="font-size:.72rem">0</span>')+'</td>'+
      '<td class="text-center"><button class="btn btn-sm btn-outline-success btn-detalle" onclick="event.stopPropagation();openDetalle('+p.id+')"><i class="bi bi-eye"></i></button></td></tr>';
  }).join('')||'<tr><td colspan="'+totalCols+'" class="text-center text-muted py-3">Sin puntos con los filtros actuales.</td></tr>';

  document.getElementById('ranking-count-badge').textContent=totalRegistros+' registros';

  /* Controles paginacion */
  let pagHtml='';
  if(totalPaginas>1){
    pagHtml+='<div class="d-flex align-items-center gap-1 flex-wrap">';
    pagHtml+='<span class="text-muted small me-2">Pag '+rankingPage+' de '+totalPaginas+'</span>';
    pagHtml+='<button class="btn btn-sm btn-outline-secondary" onclick="rankingPage=1;renderRanking(false)" '
    + (rankingPage<=1?'disabled':'')+'><i class="bi bi-chevron-double-left"></i></button>';
    pagHtml+='<button class="btn btn-sm btn-outline-secondary" onclick="rankingPage--;renderRanking(false)" '
    + (rankingPage<=1?'disabled':'')+'><i class="bi bi-chevron-left"></i></button>';
    const startP=Math.max(1,rankingPage-2);const endP=Math.min(totalPaginas,rankingPage+2);
    for(let pp=startP;pp<=endP;pp++){
      pagHtml+='<button class="btn btn-sm '+(pp===rankingPage?'btn-success':'btn-outline-secondary')
        +'" onclick="rankingPage='+pp+';renderRanking(false)">'+pp+'</button>';
    }
    pagHtml+='<button class="btn btn-sm btn-outline-secondary" onclick="rankingPage++;renderRanking(false)" '
    + (rankingPage>=totalPaginas?'disabled':'')+'><i class="bi bi-chevron-right"></i></button>';
    pagHtml+='<button class="btn btn-sm btn-outline-secondary" onclick="rankingPage='+totalPaginas+';renderRanking(false)" '
    + (rankingPage>=totalPaginas?'disabled':'')+'><i class="bi bi-chevron-double-right"></i></button>';
    pagHtml+='</div>';
  }
  document.getElementById('ranking-pagination').innerHTML=pagHtml;
}

/* ===== LISTADO - ESTADOS ===== */
function filtrarEstadosSalud(v){
  const sel=document.getElementById('est-salud-filter');if(sel){sel.value=v;}
  const selL=document.getElementById('est-loc-filter');if(selL)selL.value='';
  const selE=document.getElementById('est-estado-filter');if(selE)selE.value='';
  goToTab('estados');
}
function filtrarEstadosEstado(v){
  const sel=document.getElementById('est-estado-filter');if(sel){sel.value=v;}
  const selL=document.getElementById('est-loc-filter');if(selL)selL.value='';
  const selS=document.getElementById('est-salud-filter');if(selS)selS.value='';
  goToTab('estados');
}
function renderEstados(){
  let pts=_fitrarPtsTab('est-search-input','est-loc-filter','est-estado-filter');
  const estSalud=document.getElementById('est-salud-filter')?.value||'';
  if(estSalud)pts=pts.filter(p=>p.invEstado===estSalud);

  const totalPts=pts.length;
  const okPts=pts.filter(p=>p.invEstado==='OK').length;
  const alertPts=pts.filter(p=>p.invEstado==='Alerta').length;
  const critPts=pts.filter(p=>p.invEstado==='Critico').length;
  const inactPts=pts.filter(p=>p.estado==='Inactivo').length;
  document.getElementById('estados-stats').innerHTML=
    '<div class="col-6 col-md-3" style="cursor:pointer" onclick="filtrarEstadosSalud(\'OK\')"><div class="kpi-mini"><div class="kpi-val text-success">'+okPts+'</div><div class="kpi-lbl">OK</div></div></div>'+
    '<div class="col-6 col-md-3" style="cursor:pointer" onclick="filtrarEstadosSalud(\'Alerta\')"><div class="kpi-mini"><div class="kpi-val text-warning">'+alertPts+'</div><div class="kpi-lbl">Alerta</div></div></div>'+
    '<div class="col-6 col-md-3" style="cursor:pointer" onclick="filtrarEstadosSalud(\'Critico\')"><div class="kpi-mini"><div class="kpi-val text-danger">'+critPts+'</div><div class="kpi-lbl">Critico</div></div></div>'+
    '<div class="col-6 col-md-3" style="cursor:pointer" onclick="filtrarEstadosEstado(\'Inactivo\')"><div class="kpi-mini"><div class="kpi-val text-secondary">'+inactPts+'</div><div class="kpi-lbl">Inactivo</div></div></div>';

  if(typeof L!=='undefined'){
    if(!estadosMap){
      estadosMap=L.map('estados-map').setView([4.68,-74.10],11);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; OpenStreetMap'}).addTo(estadosMap);
    }
    estadosMap.invalidateSize();
    estadosMap.eachLayer(l=>{if(l instanceof L.Marker)estadosMap.removeLayer(l)});
    const colorMap={OK:'#198754',Alerta:'#ffc107',Critico:'#dc3545',Inactivo:'#adb5bd'};
    pts.forEach(p=>{
      const color=p.estado==='Inactivo'?'Inactivo':p.invEstado;
      const marker=L.circleMarker([p.lat,p.lng],{radius:8,fillColor:colorMap[color]||'#6c757d',color:'#fff',weight:2,opacity:1,fillOpacity:0.9}).addTo(estadosMap);
      marker.bindPopup('<div style="min-width:180px"><strong style="font-size:.85rem">'+p.nombre+'</strong><br><span style="font-size:.75rem;color:#6c757d"><i class="bi bi-geo-alt me-1"></i>'+p.direccion+'</span><br><span class="badge bg-'+(p.estado==='Activo'?'success':'secondary')+'-subtle text-'+(p.estado==='Activo'?'success':'secondary')+'" style="font-size:.65rem">'+p.estado+'</span> '+buildSaludBadge(p.invEstado)+'<br><a href="#" onclick="event.preventDefault();openDetalle('+p.id+')" class="btn btn-sm btn-outline-success mt-2" style="font-size:.72rem"><i class="bi bi-eye me-1"></i>Ver detalle</a></div>');
    });
  }

  if(typeof Chart!=='undefined'){
    destroyChart('estDist');destroyChart('estLoc');destroyChart('estGestor');
    const distCanvas=document.getElementById('chartEstDist');
    if(distCanvas){
      charts.estDist=new Chart(distCanvas,{type:'doughnut',data:{labels:['Critico','Alerta','OK'],datasets:[{data:[critPts,alertPts,okPts],backgroundColor:['#dc3545','#ffc107','#198754']}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'}}}});
    }
    const locCanvas=document.getElementById('chartEstLoc');
    if(locCanvas){
      const locData={};pts.forEach(p=>{locData[p.localidad]=(locData[p.localidad]||0)+1});
      const locEntries=Object.entries(locData).sort((a,b)=>b[1]-a[1]);
      charts.estLoc=new Chart(locCanvas,{type:'bar',data:{labels:locEntries.map(e=>e[0]),datasets:[{label:'Puntos',data:locEntries.map(e=>e[1]),backgroundColor:locEntries.map((_,i)=>['#198754','#0dcaf0','#0d6efd','#ffc107','#fd7e14','#6f42c1','#20c997'][i%7]),borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,title:{display:true,text:'puntos'}}}}});
    }

    const gestorData={};pts.forEach(p=>{gestorData[p.gestor]=(gestorData[p.gestor]||0)+1});
    const gEntries=Object.entries(gestorData).sort((a,b)=>b[1]-a[1]);
    const gestorCanvas=document.getElementById('chartEstGestor');
    if(gestorCanvas){
      charts.estGestor=new Chart(gestorCanvas,{type:'bar',data:{labels:gEntries.map(e=>e[0].substring(0,12)),datasets:[{data:gEntries.map(e=>e[1]),backgroundColor:gEntries.map((_,i)=>['#198754','#0dcaf0','#0d6efd','#ffc107','#fd7e14','#6f42c1','#20c997','#dc3545','#6610f2','#e83e8c'][i%10]),borderRadius:4}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,title:{display:true,text:'puntos'}}}}});
    }
  }

  function alertGroup(title,items,color,icon){
    if(!items.length)return'';
    return'<div class="col-12"><div class="card shadow-sm border-0"><div class="card-header bg-'+color+'-subtle border-0 px-4 py-2"><h6 class="mb-0 fw-bold text-'+color+'"><i class="bi bi-'+icon+' me-2"></i>'+title+' ('+items.length+')</h6></div><div class="card-body p-0">'+items.map(p=>'<div class="alerta-item border-bottom px-4 py-2"><div class="alerta-dot" style="background:'+(color==='danger'?'#dc3545':color==='warning'?'#ffc107':'#198754')+'"></div><div class="flex-grow-1 min-w-0"><div class="fw-semibold" style="font-size:.82rem">'+p.nombre+'</div><div class="text-muted" style="font-size:.72rem"><i class="bi bi-geo-alt me-1"></i>'+p.localidad+' — '+p.direccion+'</div><div style="font-size:.72rem" class="text-muted"><i class="bi bi-person me-1"></i>'+p.gestor+'</div></div><button class="btn btn-sm btn-outline-'+color+' flex-shrink-0" onclick="openDetalle('+p.id+')" style="font-size:.7rem"><i class="bi bi-eye"></i></button></div>').join('')+'</div></div></div>';
  }
  const activos=pts.filter(p=>p.estado==='Activo');
  const inactivos=pts.filter(p=>p.estado==='Inactivo');
  const criticos=activos.filter(p=>p.invEstado==='Critico');
  const alerta=activos.filter(p=>p.invEstado==='Alerta');
  const ok=activos.filter(p=>p.invEstado==='OK');
  document.getElementById('estados-alertas').innerHTML=
    alertGroup('Inventarios Criticos',criticos,'danger','x-circle-fill')+
    alertGroup('Inventarios en Alerta',alerta,'warning','exclamation-triangle-fill')+
    alertGroup('Inventarios OK',ok,'success','check-circle-fill')+
    alertGroup('Puntos Inactivos',inactivos,'secondary','dash-circle');
  if(!criticos.length&&!alerta.length&&!ok.length&&!inactivos.length)
    document.getElementById('estados-alertas').innerHTML='<div class="col-12 text-center py-5 text-muted">No hay puntos con los filtros actuales.</div>';
}

/* ===== LISTADO - FLUJOS ===== */
let activeFlujoSubTab='volumen';
function switchFlujoListado(sub,el){
  activeFlujoSubTab=sub;
  el.closest('ul').querySelectorAll('.nav-link').forEach(a=>a.classList.remove('active'));
  el.classList.add('active');
  ['volumen','ganancias','detalle_mat'].forEach(s=>{
    const pane=document.getElementById('flujo-sub-'+s);
    if(pane)pane.style.display=(s===sub)?'':'none';
  });
  if(sub==='volumen')renderFlujoVolumen();
  else if(sub==='ganancias')renderFlujoGanancias();
  else if(sub==='detalle_mat')renderFlujoDetalleMat();
}
function renderFlujoVolumen(){
  if(activeFlujoSubTab!=='volumen')return;
  let pts=_fitrarPtsTab('flu-search-input','flu-loc-filter',null);
  const fluMat=document.getElementById('flu-mat-filter')?.value||'';

  const ptsFlujo=pts.map(p=>{
    let flujoIn,flujoOut;
    if(fluMat){
      const items=invData.filter(x=>x.puntoId===p.id&&x.mat===fluMat);
      flujoIn=items.reduce((s,x)=>s+(x.comprasKg||0),0);
      flujoOut=items.reduce((s,x)=>s+(x.ventasKg||0),0);
    }else{
      flujoIn=flujoInPunto(p);
      flujoOut=flujoOutPunto(p);
    }
    return{...p,flujoIn,flujoOut,total:flujoIn+flujoOut};
  }).sort((a,b)=>b.total-a.total);

  if(typeof Chart!=='undefined'){
    destroyChart('flujoGeneral');
    const fCanvas=document.getElementById('chartFlujoGeneral');
    if(fCanvas){
      charts.flujoGeneral=new Chart(fCanvas,{type:'bar',data:{
        labels:ptsFlujo.map(p=>p.nombre.substring(0,14)),
        datasets:[
          {label:'Flujo In',data:ptsFlujo.map(p=>p.flujoIn),backgroundColor:'#0d6efd',borderRadius:4,barPercentage:.7},
          {label:'Flujo Out',data:ptsFlujo.map(p=>p.flujoOut),backgroundColor:'#198754',borderRadius:4,barPercentage:.7}
        ]
      },options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,title:{display:true,text:'items'}}},plugins:{legend:{position:'bottom'}}}});
    }
  }

  const totalIn=ptsFlujo.reduce((s,p)=>s+p.flujoIn,0);
  const totalOut=ptsFlujo.reduce((s,p)=>s+p.flujoOut,0);
  const mayorPunto=ptsFlujo.length?ptsFlujo[0]:null;
  document.getElementById('flujos-stats').innerHTML=
    '<div class="col-12 col-md-4"><div class="kpi-mini"><div class="kpi-val text-primary">'+totalIn.toLocaleString()+'</div><div class="kpi-lbl">Total Flujo In</div></div></div>'+
    '<div class="col-12 col-md-4"><div class="kpi-mini"><div class="kpi-val text-success">'+totalOut.toLocaleString()+'</div><div class="kpi-lbl">Total Flujo Out</div></div></div>'+
    '<div class="col-12 col-md-4"><div class="kpi-mini"><div class="kpi-val text-warning" style="font-size:1rem">'+(mayorPunto?mayorPunto.nombre:'-')+'</div><div class="kpi-lbl">Punto con Mayor Flujo</div></div></div>';
}

function renderFlujoGanancias(){
  if(activeFlujoSubTab!=='ganancias')return;
  let pts=_fitrarPtsTab('flu-gan-search-input','flu-gan-loc-filter',null);

  const ganData=pts.map(p=>{
    const items=invData.filter(x=>x.puntoId===p.id);
    const totalComprasCOP=items.reduce((s,x)=>s+(x.comprasKg||0)*x.compra,0);
    const totalVentasCOP=items.reduce((s,x)=>s+(x.ventasKg||0)*x.venta,0);
    const ganancia=totalVentasCOP-totalComprasCOP;
    const margen=totalComprasCOP?Math.round((ganancia/totalComprasCOP)*100):0;
    const matMasRentable=items.length?items.slice().sort((a,b)=>{
      const maA=(a.venta-a.compra);const maB=(b.venta-b.compra);
      return maB-maA;
    })[0]:null;
    return {...p,totalComprasCOP,totalVentasCOP,ganancia,margen,matMasRentable};
  });

  const totCompras=ganData.reduce((s,p)=>s+p.totalComprasCOP,0);
  const totVentas=ganData.reduce((s,p)=>s+p.totalVentasCOP,0);
  const totGanancia=totVentas-totCompras;
  const avgMargen=ganData.length?Math.round(ganData.reduce((s,p)=>s+p.margen,0)/ganData.length):0;
  document.getElementById('flujo-gan-stats').innerHTML=
    '<div class="col-6 col-md-3"><div class="kpi-mini"><div class="kpi-val text-primary">$'+Math.round(totCompras).toLocaleString()+'</div><div class="kpi-lbl">Total Compras</div></div></div>'+
    '<div class="col-6 col-md-3"><div class="kpi-mini"><div class="kpi-val text-success">$'+Math.round(totVentas).toLocaleString()+'</div><div class="kpi-lbl">Total Ventas</div></div></div>'+
    '<div class="col-6 col-md-3"><div class="kpi-mini"><div class="kpi-val text-'+(totGanancia>=0?'success':'danger')+'">$'+Math.round(totGanancia).toLocaleString()+'</div><div class="kpi-lbl">Ganancia Bruta</div></div></div>'+
    '<div class="col-6 col-md-3"><div class="kpi-mini"><div class="kpi-val text-warning">'+avgMargen+'%</div><div class="kpi-lbl">Margen Promedio</div></div></div>';

  const sortedGan=[...ganData].sort((a,b)=>(b.totalVentasCOP+b.totalComprasCOP)-(a.totalVentasCOP+a.totalComprasCOP));
  if(typeof Chart!=='undefined'){
    destroyChart('flujoGanancias');
    const gCanvas=document.getElementById('chartFlujoGanancias');
    if(gCanvas){
      charts.flujoGanancias=new Chart(gCanvas,{type:'bar',data:{
        labels:sortedGan.map(p=>p.nombre.substring(0,14)),
        datasets:[
          {label:'Compras ($)',data:sortedGan.map(p=>p.totalComprasCOP),backgroundColor:'#0d6efd',borderRadius:4,barPercentage:.7},
          {label:'Ventas ($)',data:sortedGan.map(p=>p.totalVentasCOP),backgroundColor:'#198754',borderRadius:4,barPercentage:.7}
        ]
      },options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,title:{display:true,text:'$ COP'}}},plugins:{legend:{position:'bottom'}}}});
    }
  }

  if(typeof Chart!=='undefined'){
    destroyChart('flujoMargenRank');
    const margenPts=[...ganData].sort((a,b)=>b.margen-a.margen);
    const top5m=margenPts.slice(0,5);
    const bot5m=margenPts.slice(-5).reverse();
    const margenCombined=[...top5m,{nombre:'——',margen:0,totalComprasCOP:0,totalVentasCOP:0,ganancia:0},...bot5m];
    const mrCanvas=document.getElementById('chartFlujoMargenRank');
    if(mrCanvas){
      charts.flujoMargenRank=new Chart(mrCanvas,{type:'bar',data:{labels:margenCombined.map(d=>d.nombre.substring(0,14)),datasets:[{label:'Margen %',data:margenCombined.map(d=>d.margen),backgroundColor:margenCombined.map(d=>d.nombre==='——'?'transparent':d.margen>=0?'#198754':'#dc3545'),borderRadius:4}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,title:{display:true,text:'%'}}}}});
    }
  }

  const topGanData=[...ganData].sort((a,b)=>b.ganancia-a.ganancia).slice(0,10);
  document.getElementById('flujo-gan-tabla-mat').innerHTML='<table class="table table-sm table-hover align-middle mb-0"><thead class="table-light"><tr><th>Punto</th><th>Localidad</th><th>Material</th><th>Margen $/u</th><th>Ganancia Total</th></tr></thead><tbody>'+
    topGanData.map(p=>{
      const mat=p.matMasRentable;
      const margenUnit=mat?mat.venta-mat.compra:0;
      return'<tr><td class="fw-semibold" style="font-size:.78rem">'+p.nombre.substring(0,16)+'</td><td style="font-size:.75rem;color:#6c757d">'+p.localidad+'</td><td style="font-size:.75rem">'+(mat?mat.mat:'N/A')+'</td><td style="font-size:.82rem" class="fw-bold '+(margenUnit>=0?'text-success':'text-danger')+'">$'+(mat?Math.round(margenUnit).toLocaleString():'0')+'</td><td style="font-size:.82rem" class="fw-bold '+(p.ganancia>=0?'text-success':'text-danger')+'">$'+Math.round(p.ganancia).toLocaleString()+'</td></tr>';
    }).join('')+'</tbody></table>';
}

function renderFlujoDetalleMat(){
  if(activeFlujoSubTab!=='detalle_mat')return;
  let pts=_fitrarPtsTab('flu-det-search-input','flu-det-loc-filter',null);
  const fluDetMat=document.getElementById('flu-det-mat-filter')?.value||'';

  const allMaterials=[...new Set(invData.map(x=>x.mat))].sort();
  let filteredMaterials=fluDetMat?[fluDetMat]:allMaterials;

  let totalGananciaCOP=0,totalVolumen=0;
  const matRanking=filteredMaterials.map(mat=>{
    let gananciaMat=0,volumenMat=0;
    pts.forEach(p=>{
      const items=invData.filter(x=>x.puntoId===p.id&&x.mat===mat);
      gananciaMat+=items.reduce((s,x)=>s+(x.ventasKg||0)*x.venta-(x.comprasKg||0)*x.compra,0);
      volumenMat+=items.reduce((s,x)=>s+(x.ventasKg||0),0);
    });
    totalGananciaCOP+=gananciaMat;
    totalVolumen+=volumenMat;
    return{mat,ganancia:Math.round(gananciaMat),volumen:Math.round(volumenMat)};
  }).sort((a,b)=>b.ganancia-a.ganancia);

  const topMat=matRanking.length?matRanking[0]:null;
  const topVol=matRanking.length?[...matRanking].sort((a,b)=>b.volumen-a.volumen)[0]:null;
  const ptsCount=pts.length;
  document.getElementById('flujo-det-stats').innerHTML=
    '<div class="col-6 col-md-3"><div class="kpi-mini"><div class="kpi-val text-success">'+(topMat?topMat.mat:'-')+'</div><div class="kpi-lbl">Mat #1 en Ganancias</div></div></div>'+
    '<div class="col-6 col-md-3"><div class="kpi-mini"><div class="kpi-val text-primary">'+(topVol?topVol.mat:'-')+'</div><div class="kpi-lbl">Mat #1 en Volumen</div></div></div>'+
    '<div class="col-6 col-md-3"><div class="kpi-mini"><div class="kpi-val text-warning">$'+Math.round(totalGananciaCOP).toLocaleString()+'</div><div class="kpi-lbl">Total Ganancia</div></div></div>'+
    '<div class="col-6 col-md-3"><div class="kpi-mini"><div class="kpi-val text-info">'+ptsCount+'</div><div class="kpi-lbl">Puntos Activos</div></div></div>';

  if(typeof Chart!=='undefined'){
    destroyChart('flujoDetalleMat');
    const dmCanvas=document.getElementById('chartFlujoDetalleMat');
    if(dmCanvas){
      const topPts=[...pts].sort((a,b)=>{
        const totalA=invData.filter(x=>x.puntoId===a.id).reduce((s,x)=>s+(x.ventasKg||0)*x.venta,0);
        const totalB=invData.filter(x=>x.puntoId===b.id).reduce((s,x)=>s+(x.ventasKg||0)*x.venta,0);
        return totalB-totalA;
      }).slice(0,8);
      const colors=['#0d6efd','#198754','#dc3545','#ffc107','#0dcaf0','#6f42c1','#fd7e14','#20c997','#e83e8c'];
      const datasets=filteredMaterials.slice(0,5).map((mat,mi)=>({
        label:mat,data:topPts.map(p=>{
          const items=invData.filter(x=>x.puntoId===p.id&&x.mat===mat);
          return Math.round(items.reduce((s,x)=>s+(x.ventasKg||0)*x.venta,0));
        }),backgroundColor:colors[mi%colors.length],borderRadius:0
      }));
      charts.flujoDetalleMat=new Chart(dmCanvas,{type:'bar',data:{labels:topPts.map(p=>p.nombre.substring(0,14)),datasets:datasets},options:{responsive:true,maintainAspectRatio:false,scales:{x:{stacked:true},y:{stacked:true,beginAtZero:true,title:{display:true,text:'$ COP'}}},plugins:{legend:{position:'bottom'}}}});
    }
  }

  document.getElementById('flujo-det-tabla').innerHTML='<table class="table table-sm table-hover align-middle mb-0"><thead class="table-light"><tr><th>#</th><th>Material</th><th>Ganancia Total</th><th>Volumen Total</th><th>Margen Prom</th></tr></thead><tbody>'+
    matRanking.map((m,i)=>{
      let totalCompras=0,totalVentas=0;
      filteredMaterials.forEach(mat=>{
        pts.forEach(p=>{
          const items=invData.filter(x=>x.puntoId===p.id&&x.mat===mat);
          totalCompras+=items.reduce((s,x)=>s+(x.comprasKg||0)*x.compra,0);
          totalVentas+=items.reduce((s,x)=>s+(x.ventasKg||0)*x.venta,0);
        });
      });
      const margenProm=totalCompras?Math.round(((totalVentas-totalCompras)/totalCompras)*100):0;
      return'<tr><td class="fw-bold text-muted">'+(i+1)+'</td><td class="fw-semibold" style="font-size:.82rem">'+m.mat+'</td><td class="fw-bold '+(m.ganancia>=0?'text-success':'text-danger')+'" style="font-size:.82rem">$'+m.ganancia.toLocaleString()+'</td><td style="font-size:.82rem">'+m.volumen.toLocaleString()+' u</td><td style="font-size:.82rem">'+margenProm+'%</td></tr>';
    }).join('')+'</tbody></table>';
}

/* ===== LISTADO - MENSAJES ===== */
let msgsPage=1,msgsPerPage=20;
function renderMensajesListado(resetPage){
  if(resetPage!==false)msgsPage=1;
  const convs=conversaciones.slice();
  const totalConvs=convs.length;
  const totalMsgs=convs.reduce((s,c)=>s+(c.msgs||0),0);

  document.getElementById('msgs-stats').innerHTML=
    '<div class="col-6 col-md-4"><div class="kpi-mini"><div class="kpi-val text-primary">'+totalConvs+'</div><div class="kpi-lbl">Total Convers.</div></div></div>'+
    '<div class="col-6 col-md-4"><div class="kpi-mini"><div class="kpi-val text-info">'+totalMsgs+'</div><div class="kpi-lbl">Total Mensajes</div></div></div>'+
    '<div class="col-6 col-md-4"><div class="kpi-mini"><div class="kpi-val text-danger">'+(convs.length)+'</div><div class="kpi-lbl">Chats Activos</div></div></div>';

  if(typeof Chart!=='undefined'){
    destroyChart('msgsTopChats');
    const msgsCanvas=document.getElementById('chartMsgsTopChats');
    if(msgsCanvas){
      const topChats=[...puntos].sort((a,b)=>b.msgs-a.msgs).slice(0,10);
      charts.msgsTopChats=new Chart(msgsCanvas,{type:'bar',data:{labels:topChats.map(p=>p.nombre.substring(0,14)),datasets:[{label:'Mensajes',data:topChats.map(p=>p.msgs),backgroundColor:topChats.map((_,i)=>['#0d6efd','#198754','#ffc107','#dc3545','#0dcaf0','#6f42c1','#fd7e14','#20c997','#e83e8c','#6610f2'][i%10]),borderRadius:4}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,title:{display:true,text:'mensajes'}}}}});
    }
  }

  const totalPaginas=Math.ceil(totalConvs/msgsPerPage);
  if(msgsPage>totalPaginas)msgsPage=totalPaginas||1;
  const inicio=(msgsPage-1)*msgsPerPage;
  const pagina=convs.slice(inicio,inicio+msgsPerPage);

  document.getElementById('msgs-tbody').innerHTML=pagina.map((c,i)=>'<tr><td class="fw-bold text-muted">'+(inicio+i+1)+'</td><td class="fw-semibold" style="font-size:.82rem">'+c.punto+'</td><td style="font-size:.78rem">'+c.ciudadano+'</td><td style="font-size:.78rem;color:#6c757d">'+c.fecha+'</td><td class="text-center">'+c.msgs+'</td><td style="font-size:.78rem;max-width:200px" class="text-truncate">'+c.ultimo+'</td></tr>').join('')||'<tr><td colspan="6" class="text-center text-muted py-3">Sin conversaciones.</td></tr>';
  document.getElementById('msgs-count-badge').textContent=totalConvs+' conversaciones';

  let pagHtml='';
  if(totalPaginas>1){
    pagHtml+='<div class="d-flex align-items-center gap-1 flex-wrap">';
    pagHtml+='<span class="text-muted small me-2">Pag '+msgsPage+' de '+totalPaginas+'</span>';
    pagHtml+='<button class="btn btn-sm btn-outline-secondary" onclick="msgsPage=1;renderMensajesListado(false)" '+(msgsPage<=1?'disabled':'')+'><i class="bi bi-chevron-double-left"></i></button>';
    pagHtml+='<button class="btn btn-sm btn-outline-secondary" onclick="msgsPage--;renderMensajesListado(false)" '+(msgsPage<=1?'disabled':'')+'><i class="bi bi-chevron-left"></i></button>';
    const startP=Math.max(1,msgsPage-2);const endP=Math.min(totalPaginas,msgsPage+2);
    for(let pp=startP;pp<=endP;pp++){
      pagHtml+='<button class="btn btn-sm '+(pp===msgsPage?'btn-success':'btn-outline-secondary')+'" onclick="msgsPage='+pp+';renderMensajesListado(false)">'+pp+'</button>';
    }
    pagHtml+='<button class="btn btn-sm btn-outline-secondary" onclick="msgsPage++;renderMensajesListado(false)" '+(msgsPage>=totalPaginas?'disabled':'')+'><i class="bi bi-chevron-right"></i></button>';
    pagHtml+='<button class="btn btn-sm btn-outline-secondary" onclick="msgsPage='+totalPaginas+';renderMensajesListado(false)" '+(msgsPage>=totalPaginas?'disabled':'')+'><i class="bi bi-chevron-double-right"></i></button>';
    pagHtml+='</div>';
  }
  document.getElementById('msgs-pagination').innerHTML=pagHtml;
}

/* ===== DETALLE - TABS ===== */
function switchTab(tab,el){
  el.closest('ul').querySelectorAll('.nav-link').forEach(a=>a.classList.remove('active'));
  el.classList.add('active');
  document.querySelectorAll('#vista-detalle .tab-pane').forEach(p=>p.classList.remove('show','active'));
  const pane=document.getElementById('tab-'+tab);
  if(pane)pane.classList.add('show','active');
  if(tab==='inventario')renderInventario();
  else if(tab==='historial')renderHistorial();
  else if(tab==='flujo')renderFlujo();
  else if(tab==='calendario')renderCalendario();
  else if(tab==='mensajes')renderMensajes();
}

function renderInventario(){
  if(!currentPuntoId)return;
  const items=invData.filter(x=>x.puntoId===currentPuntoId);
  const totalStock=items.reduce((s,x)=>s+x.stock,0);
  const totalCap=items.reduce((s,x)=>s+x.cap,0);
  const capProm=items.length?Math.round(totalCap/items.length):0;
  const bajoStock=items.filter(x=>x.stock/x.cap<.3).length;
  const p=puntos.find(x=>x.id===currentPuntoId);

  document.getElementById('inv-total-stock').textContent=totalCap?Math.round((totalStock/totalCap)*100)+'%':'0%';
  document.getElementById('inv-total-materiales').textContent=items.length;
  document.getElementById('inv-capacidad-prom').textContent=capProm.toLocaleString()+' u';
  document.getElementById('inv-bajo-stock').textContent=bajoStock;

  if(typeof Chart!=='undefined'){
    destroyChart('invCategorias');destroyChart('invStock');destroyChart('invMargen');
    const catData={};items.forEach(x=>{catData[x.cat]=(catData[x.cat]||0)+x.stock});
    const catEntries=Object.entries(catData).sort((a,b)=>b[1]-a[1]);
    const ccCanvas=document.getElementById('chartInvCategorias');
    if(ccCanvas){
      charts.invCategorias=new Chart(ccCanvas,{type:'doughnut',data:{labels:catEntries.map(e=>e[0]),datasets:[{data:catEntries.map(e=>e[1]),backgroundColor:['#198754','#0d6efd','#ffc107','#dc3545','#0dcaf0','#6f42c1']}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'}}}});
    }
    const csCanvas=document.getElementById('chartInvStock');
    if(csCanvas){
      charts.invStock=new Chart(csCanvas,{type:'bar',data:{labels:items.map(x=>x.mat),datasets:[{label:'% Ocupacion',data:items.map(x=>Math.round(x.stock/x.cap*100)),backgroundColor:items.map(x=>x.stock/x.cap<.3?'#dc3545':x.stock/x.cap<.5?'#ffc107':'#198754'),borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,title:{display:true,text:'%'}}}}});
    }
    const cmCanvas=document.getElementById('chartInvMargen');
    if(cmCanvas){
      charts.invMargen=new Chart(cmCanvas,{type:'bar',data:{labels:items.map(x=>x.mat),datasets:[{label:'Margen',data:items.map(x=>x.venta-x.compra),backgroundColor:items.map(x=>(x.venta-x.compra)>=0?'#198754':'#dc3545'),borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,title:{display:true,text:'$'}}}}});
    }
  }

  document.getElementById('inv-cards').innerHTML=items.map(x=>{
    const pct=Math.round(x.stock/x.cap*100);
    const margenUnit=x.venta-x.compra;
    const ventasCOP=x.ventasKg*x.venta;
    const comprasCOP=x.comprasKg*x.compra;
    return'<div class="col-12 col-md-6 col-lg-4"><div class="inv-card" onclick="this.classList.toggle(\'selected\')"><div class="d-flex justify-content-between align-items-start mb-2"><div class="fw-semibold" style="font-size:.82rem">'+x.mat+'</div>'+buildSaludBadge(x.estado)+'</div><div class="inv-summary">Stock: '+x.stock+' / '+x.cap+' u</div><div class="stock-bar"><div class="stock-bar-fill" style="width:'+Math.round(x.stock/x.cap*100)+'%;background:'+(pct<30?'#dc3545':pct<50?'#ffc107':'#198754')+'"></div></div><div class="d-flex justify-content-between mt-2" style="font-size:.7rem"><span class="text-muted">Compra: $'+x.compra+'</span><span class="text-muted">Venta: $'+x.venta+'</span><span class="fw-bold '+(margenUnit>=0?'text-success':'text-danger')+'">Margen: $'+margenUnit.toLocaleString()+'</span></div><div class="d-flex justify-content-between mt-1" style="font-size:.68rem"><span class="text-muted">Periodo: '+x.comprasKg+' / '+x.ventasKg+' u</span><span class="text-muted">Ult: '+x.ultimoMov+'</span></div></div></div>';
  }).join('')||'<div class="col-12 text-center text-muted py-3">Sin inventario para este punto.</div>';
}

function renderHistorial(){
  if(!currentPuntoId)return;
  const movs=historial.filter(h=>h.puntoId===currentPuntoId);
  document.getElementById('hist-compras').textContent=movs.filter(m=>m.tipo==='Compra').length;
  document.getElementById('hist-ventas').textContent=movs.filter(m=>m.tipo==='Venta').length;
  document.getElementById('hist-total').textContent=movs.length;
  document.getElementById('hist-kg').textContent=movs.reduce((s,m)=>s+m.kg,0).toLocaleString();

  document.getElementById('hist-tbody').innerHTML=movs.map(m=>{
    const items=invData.filter(x=>x.puntoId===currentPuntoId&&x.mat===m.mat);
    const inv=items.length?items[0]:null;
    const margenUnit=inv?inv.venta-inv.compra:0;
    const margen=inv?Math.round(margenUnit*m.kg*100)/100:0;
    return'<tr><td style="font-size:.78rem;color:#6c757d">'+m.fecha+'</td><td><span class="mov-tipo '+(m.tipo==='Compra'?'mov-compra':'mov-venta')+'"><i class="bi bi-'+(m.tipo==='Compra'?'arrow-down-circle':'arrow-up-circle')+'"></i> '+m.tipo+'</span></td><td style="font-size:.8rem" class="fw-semibold">'+m.mat+'</td><td style="font-size:.8rem">'+m.kg+' u</td><td style="font-size:.8rem">$'+(inv?inv.compra:'-')+'</td><td style="font-size:.8rem">$'+m.valor.toLocaleString()+'</td><td style="font-size:.8rem" class="fw-bold '+(margen>=0?'text-success':'text-danger')+'">$'+margen.toLocaleString()+'</td><td style="font-size:.72rem;color:#6c757d">—</td></tr>';
  }).join('')||'<tr><td colspan="8" class="text-center text-muted py-3">Sin movimientos para este punto.</td></tr>';
}

function switchFlujo(sub,el){
  el.closest('ul').querySelectorAll('.nav-link').forEach(a=>a.classList.remove('active'));
  el.classList.add('active');
  if(sub==='stock')renderFlujo();
  else if(sub==='ganancias')renderFlujoGananciasDetalle();
  else if(sub==='precios')renderFlujoPrecios();
}

function renderFlujo(){
  if(!currentPuntoId)return;
  const p=puntos.find(x=>x.id===currentPuntoId);if(!p)return;
  const items=invData.filter(x=>x.puntoId===currentPuntoId);
  const totalStock=items.reduce((s,x)=>s+x.stock,0);
  const totalCompras=items.reduce((s,x)=>s+x.comprasKg,0);
  const totalVentas=items.reduce((s,x)=>s+x.ventasKg,0);
  const utilidad=items.reduce((s,x)=>s+(x.ventasKg||0)*x.venta-(x.comprasKg||0)*x.compra,0);

  document.getElementById('flujo-actual').textContent=totalStock.toLocaleString()+' u';
  document.getElementById('flujo-compras').textContent='$'+totalCompras.toLocaleString();
  document.getElementById('flujo-ventas-k').textContent='$'+totalVentas.toLocaleString();
  document.getElementById('flujo-utilidad').textContent='$'+Math.round(utilidad).toLocaleString();

  if(typeof Chart!=='undefined'){
    destroyChart('flujo');
    const fCanvas=document.getElementById('chartFlujo');
    if(fCanvas){
      const dias=['Lun','Mar','Mie','Jue','Vie','Sab','Dom'];
      const comprasSim=dias.map(()=>Math.round(Math.random()*500+100));
      const ventasSim=dias.map(()=>Math.round(Math.random()*400+80));
      charts.flujo=new Chart(fCanvas,{type:'line',data:{labels:dias,datasets:[
        {label:'Compras',data:comprasSim,borderColor:'#0d6efd',backgroundColor:'rgba(13,110,253,.05)',fill:true,tension:.4},
        {label:'Ventas',data:ventasSim,borderColor:'#dc3545',backgroundColor:'rgba(220,53,69,.05)',fill:true,tension:.4}
      ]},options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,title:{display:true,text:'$ COP'}}},plugins:{legend:{position:'bottom'}}}});
    }
  }
}

function renderFlujoGananciasDetalle(){
  renderFlujo();
}

function renderFlujoPrecios(){
  renderFlujo();
}

function renderCalendario(){
  if(!currentPuntoId)return;
  const evs=eventos.filter(e=>e.puntoId===currentPuntoId);
  document.getElementById('cal-completados').textContent=evs.filter(e=>e.es_completado).length;
  document.getElementById('cal-pendientes').textContent=evs.filter(e=>!e.es_completado).length;
  const ahora=new Date();
  const prox7d=evs.filter(e=>{const d=new Date(e.fecha);return!e.es_completado&&(d-ahora)/(1000*86400)<=7&&(d-ahora)/(1000*86400)>=0;}).length;
  document.getElementById('cal-proximos').textContent=prox7d;

  document.getElementById('cal-eventos').innerHTML=evs.sort((a,b)=>new Date(a.fecha)-new Date(b.fecha)).map(e=>
    '<div class="event-item '+(e.es_completado?'event-completado':'event-pendiente')+'"><div class="d-flex justify-content-between align-items-start"><div><div class="fw-semibold" style="font-size:.82rem">'+e.titulo+'</div><div class="inv-summary"><i class="bi bi-calendar me-1"></i>'+e.fecha+' — <span class="badge bg-info-subtle text-info" style="font-size:.65rem">'+e.tipo+'</span></div></div><span class="badge bg-'+(e.es_completado?'success':'warning')+'-subtle text-'+(e.es_completado?'success':'warning')+'" style="font-size:.65rem">'+(e.es_completado?'Completado':'Pendiente')+'</span></div></div>'
  ).join('')||'<div class="text-center text-muted py-3">Sin eventos para este punto.</div>';
}

function renderMensajes(){
  if(!currentPuntoId)return;
  const convs=conversaciones.filter(c=>c.puntoId===currentPuntoId);
  const p=puntos.find(x=>x.id===currentPuntoId);
  document.getElementById('msg-total').textContent=convs.length;
  document.getElementById('msg-total-msgs').textContent=convs.reduce((s,c)=>s+(c.msgs||0),0);
  document.getElementById('msg-no-leidos').textContent=convs.length;

  document.getElementById('msg-list').innerHTML='<div class="table-responsive"><table class="table table-sm table-hover align-middle mb-0"><thead class="table-light"><tr><th>#</th><th>Ciudadano</th><th>Fecha</th><th>Msgs</th><th>Ultimo Mensaje</th></tr></thead><tbody>'+
    convs.map((c,i)=>'<tr><td class="fw-bold text-muted">'+(i+1)+'</td><td class="fw-semibold" style="font-size:.82rem">'+c.ciudadano+'</td><td style="font-size:.78rem;color:#6c757d">'+c.fecha+'</td><td class="text-center">'+c.msgs+'</td><td style="font-size:.78rem;max-width:220px" class="text-truncate">'+c.ultimo+'</td></tr>').join('')+
    '</tbody></table></div>';
}

/* ===== MODAL EDITAR ===== */
function openEditModal(){
  if(!currentPuntoId)return;
  const p=puntos.find(x=>x.id===currentPuntoId);if(!p)return;
  document.getElementById('edit-nombre').value=p.nombre;
  document.getElementById('edit-direccion').value=p.direccion;
  document.getElementById('edit-localidad').value=p.localidad;
  document.getElementById('edit-gestor').value=p.gestor;
  document.getElementById('edit-estado').value=p.estado;
  document.getElementById('edit-capacidad').value=p.capMax;
  new bootstrap.Modal(document.getElementById('editPuntoModal')).show();
}
function guardarEdicionPunto(){
  const p=puntos.find(x=>x.id===currentPuntoId);if(!p)return;
  p.nombre=document.getElementById('edit-nombre').value;
  p.direccion=document.getElementById('edit-direccion').value;
  p.localidad=document.getElementById('edit-localidad').value;
  p.gestor=document.getElementById('edit-gestor').value;
  p.estado=document.getElementById('edit-estado').value;
  p.capMax=parseInt(document.getElementById('edit-capacidad').value)||p.capMax;
  const modal=bootstrap.Modal.getInstance(document.getElementById('editPuntoModal'));
  if(modal)modal.hide();
  renderKPIs();
  openDetalle(currentPuntoId);
}

/* ===== CLEAR FILTERS POR TAB ===== */
function _clearInput(id){const el=document.getElementById(id);if(el)el.value='';}
function _clearSelect(id){if(typeof $!=='undefined'){$('#'+id).val('').trigger('change');}else{const el=document.getElementById(id);if(el)el.value='';}}
function limpiarFiltrosResumen(){_clearInput('res-search-input');_clearSelect('res-loc-filter');_clearSelect('res-estado-filter');_clearSelect('res-mat-filter');document.getElementById('res-orden').value='mov';renderResumen();}
function limpiarFiltrosEstados(){_clearInput('est-search-input');_clearSelect('est-loc-filter');_clearSelect('est-estado-filter');_clearSelect('est-salud-filter');renderEstados();}
function limpiarFiltrosFlujoVolumen(){_clearInput('flu-search-input');_clearSelect('flu-loc-filter');_clearSelect('flu-mat-filter');renderFlujoVolumen();}
function limpiarFiltrosFlujoGanancias(){_clearInput('flu-gan-search-input');_clearSelect('flu-gan-loc-filter');renderFlujoGanancias();}
function limpiarFiltrosFlujoDetalleMat(){_clearInput('flu-det-search-input');_clearSelect('flu-det-loc-filter');_clearSelect('flu-det-mat-filter');renderFlujoDetalleMat();}

/* ===== BOOT ===== */
populatePanelFilters();
if(typeof $!=='undefined'){$('.js-select2').select2({theme:'bootstrap-5',width:'auto',placeholder:function(){return $(this).find('option:first').text()||'Selecciona...';}});}
renderKPIs();
renderResumen();
renderRanking();

/* === populate filters === */
function populatePanelFilters(){
  const locs=[...new Set(puntos.map(p=>p.localidad))].sort();
  const mats=[...new Set(invData.map(x=>x.mat))].sort();

  // Resumen
  const resLoc=document.getElementById('res-loc-filter');
  if(resLoc)locs.forEach(l=>{const o=document.createElement('option');o.value=l;o.textContent=l;resLoc.appendChild(o)});
  const resMat=document.getElementById('res-mat-filter');
  if(resMat)mats.forEach(m=>{const o=document.createElement('option');o.value=m;o.textContent=m;resMat.appendChild(o)});

  // Estados tab
  const estLoc=document.getElementById('est-loc-filter');
  if(estLoc)locs.forEach(l=>{const o=document.createElement('option');o.value=l;o.textContent=l;estLoc.appendChild(o)});

  // Flujo filters
  const fluLoc=document.getElementById('flu-loc-filter');
  if(fluLoc)locs.forEach(l=>{const o=document.createElement('option');o.value=l;o.textContent=l;fluLoc.appendChild(o)});
  const fluMat=document.getElementById('flu-mat-filter');
  if(fluMat)mats.forEach(m=>{const o=document.createElement('option');o.value=m;o.textContent=m;fluMat.appendChild(o)});

  // Ganancias
  const fluGanLoc=document.getElementById('flu-gan-loc-filter');
  if(fluGanLoc)locs.forEach(l=>{const o=document.createElement('option');o.value=l;o.textContent=l;fluGanLoc.appendChild(o)});

  // Detalle mat
  const fluDetLoc=document.getElementById('flu-det-loc-filter');
  if(fluDetLoc)locs.forEach(l=>{const o=document.createElement('option');o.value=l;o.textContent=l;fluDetLoc.appendChild(o)});
  const fluDetMat=document.getElementById('flu-det-mat-filter');
  if(fluDetMat)mats.forEach(m=>{const o=document.createElement('option');o.value=m;o.textContent=m;fluDetMat.appendChild(o)});

  // Ranking filters
  const rankLoc=document.getElementById('rank-flt-localidad');
  if(rankLoc)locs.forEach(l=>{const o=document.createElement('option');o.value=l;o.textContent=l;rankLoc.appendChild(o)});

  // Inventario filters
  const cats=[...new Set(invData.map(x=>x.cat))].sort();
  const invCat=document.getElementById('inv-cat-filter');
  if(invCat)cats.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;invCat.appendChild(o)});

  // Historial materials
  const histMat=document.getElementById('hist-material-filter');
  if(histMat)mats.forEach(m=>{const o=document.createElement('option');o.value=m;o.textContent=m;histMat.appendChild(o)});
}
