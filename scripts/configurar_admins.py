import os
from django.contrib.auth import get_user_model
from apps.publicaciones.models import Publicacion
from config import constants

User = get_user_model()

PASS = os.environ.get('ADMIN_PASSWORD', 'Admin123*')

# ============================================================
# 1. ELIAN MELO: renombrar y eliminar duplicado
# ============================================================
elian = User.objects.filter(email="admin@inforecicla.com").first()
if elian:
    elian.email = "admin_elian@inforecicla.com"
    elian.tipo_usuario = constants.TipoUsuario.ADMIN
    elian.is_staff = True
    elian.is_superuser = True
    elian.is_active = True
    elian.set_password(PASS)
    elian.save()
    print("✓ Elian: email → admin_elian@inforecicla.com, password actualizado")

# Eliminar el otro admin duplicado
User.objects.filter(email="admin@gmail.com").delete()
print("  Eliminado admin duplicado: admin@gmail.com")

# ============================================================
# 2. JORGE BARRERA: CIU → ADM con nuevo email
# ============================================================
jorge = User.objects.filter(email="relcrack590@gmail.com").first()
if jorge:
    old_email = jorge.email
    jorge.email = "admin_jorge@inforecicla.com"
    jorge.tipo_usuario = constants.TipoUsuario.ADMIN
    jorge.is_staff = True
    jorge.is_superuser = True
    jorge.is_active = True
    jorge.nombres = "Jorge"
    jorge.apellidos = "Barrera"
    jorge.set_password(PASS)
    jorge.save()
    print(f"✓ Jorge: {old_email} → admin_jorge@inforecicla.com (ADM), password actualizado")

# ============================================================
# 3. ANDRÉS SALAS: CIU → ADM con nuevo email
# ============================================================
andres = User.objects.filter(email="andresmadid1206@gmail.com").first()
if andres:
    old_email = andres.email
    andres.email = "admin_andres@inforecicla.com"
    andres.tipo_usuario = constants.TipoUsuario.ADMIN
    andres.is_staff = True
    andres.is_superuser = True
    andres.is_active = True
    andres.nombres = "Andrés"
    andres.apellidos = "Salas"
    andres.set_password(PASS)
    andres.save()
    print(f"✓ Andrés: {old_email} → admin_andres@inforecicla.com (ADM), password actualizado")

# ============================================================
# 4. REASIGNAR autoría de publicaciones
# ============================================================
elian = User.objects.filter(email="admin_elian@inforecicla.com").first()
jorge = User.objects.filter(email="admin_jorge@inforecicla.com").first()
andres = User.objects.filter(email="admin_andres@inforecicla.com").first()

pubs = list(Publicacion.objects.all().order_by("fecha_creacion"))
print(f"\nReasignando {len(pubs)} publicaciones...")

# Elian: 4 (incluye la inactiva)
for p in pubs[:4]:
    p.usuario = elian
    p.save()
    print(f"  Elian ← {p.titulo[:55]}")

# Andrés: 3
for p in pubs[4:7]:
    p.usuario = andres
    p.save()
    print(f"  Andrés ← {p.titulo[:55]}")

# Jorge: 3
for p in pubs[7:10]:
    p.usuario = jorge
    p.save()
    print(f"  Jorge  ← {p.titulo[:55]}")

print("\n✅ Configuración completada")
