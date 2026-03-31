from groq import Groq
from django.conf import settings
from apps.inventory.models import Inventario


class AsistenteECAService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama3-8b-8192"  # Balance perfecto entre velocidad y razonamiento

    def generar_contexto_eca(self, punto_eca):
        """
        Extrae los datos fácticos del Punto ECA específico para alimentar a la IA.
        Aquí es donde aplicamos la restricción de datos.
        """
        items = Inventario.objects.filter(punto_eca=punto_eca).select_related(
            "material"
        )

        contexto = f"Datos del Punto ECA '{punto_eca.nombre}':\n"
        contexto += "Inventario actual:\n"

        if not items.exists():
            contexto += "- El inventario está vacío actualmente.\n"
        else:
            for item in items:
                contexto += (
                                f"- {item.material.nombre}: {item.stock_actual} unidades disponibles.\n"
                )

        return contexto

    def consultar(self, punto_eca, pregunta_usuario):
        # Generar la base de conocimientos en tiempo real
        contexto_real = self.generar_contexto_eca(punto_eca)

        # Prompt de Sistema: Define el comportamiento y los límites
        system_message = {
            "role": "system",
            "content": (
                "Eres el Asistente Virtual de Inforecicla. Tu función es ayudar al gestor del Punto ECA "
                "a entender su inventario y operaciones. "
                f"Solo tienes acceso a los siguientes datos reales: {contexto_real}. "
                "REGLAS: 1. Si te preguntan por datos que no están en el contexto, responde que no tienes acceso. "
                "2. Sé breve y profesional. 3. No menciones el término 'contexto' al usuario."
            ),
        }

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message["content"]},
                    {"role": "user", "content": pregunta_usuario}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=500,
            )
            return chat_completion.choices[0].message.content
        except Exception:
            # Si ocurre un error con la API, devolvemos un mensaje amigable
            return "Lo siento, hubo un problema al consultar la IA. Intentalo otra vez o contacta al soporte."
