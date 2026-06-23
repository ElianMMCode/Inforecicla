import os
from django.contrib.auth import get_user_model
from apps.ecas.models import PuntoECA
from config import constants

User = get_user_model()

# Gestores nuevos para asignar a ECAs sin gestor
PASS = os.environ.get('ADMIN_PASSWORD', 'Admin123*')

nuevos_gestores = [
    ("andrea.lopez@inforecicla.com", "Andrea", "López", "3002220001"),
    ("carlos.martinez@inforecicla.com", "Carlos", "Martínez", "3002220002"),
    ("diana.perez@inforecicla.com", "Diana", "Pérez", "3002220003"),
    ("fernando.garcia@inforecicla.com", "Fernando", "García", "3002220004"),
    ("lucia.ramirez@inforecicla.com", "Lucía", "Ramírez", "3002220005"),
    ("javier.torres@inforecicla.com", "Javier", "Torres", "3002220006"),
]

gestores_creados = []
for email, nom, ape, cel in nuevos_gestores:
    user = User.objects.filter(email=email).first()
    if user:
        print(f"  Ya existe: {email}")
    else:
        user = User.objects.create_user(
            email=email,
            password=PASS,
            nombres=nom,
            apellidos=ape,
            celular=cel,
            tipo_usuario=constants.TipoUsuario.GESTOR_ECA,
            is_active=True,
            is_staff=True,
        )
        print(f"✓ Creado GECA: {email} ({nom} {ape})")
    gestores_creados.append(user)

# ECAs sin gestor ordenadas
ecas_sin_gestor = list(PuntoECA.objects.filter(gestor_eca__isnull=True).order_by("localidad__nombre"))

print(f"\nECAs sin gestor: {len(ecas_sin_gestor)}")
print(f"Gestores disponibles: {len(gestores_creados)}")

# Asignar los 6 nuevos gestores a 6 ECAs, dejando 5 sin gestor
for i, eca in enumerate(ecas_sin_gestor[:6]):
    eca.gestor_eca = gestores_creados[i]
    eca.save()
    print(f"  Asignado {gestores_creados[i].email} → {eca.nombre}")

restantes = PuntoECA.objects.filter(gestor_eca__isnull=True).count()
print(f"\n✅ ECAs sin gestor restantes: {restantes}")
