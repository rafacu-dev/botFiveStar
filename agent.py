from __future__ import annotations

import logging
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai


load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("Agent")
logger.setLevel(logging.INFO)


async def entrypoint(ctx: JobContext):
    ctx.room.remote_participants
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()

    run_multimodal_agent(ctx, participant)

    logger.info("agent started")


def run_multimodal_agent(ctx: JobContext, participant: rtc.Participant):
    logger.info("starting multimodal agent")

    model = openai.realtime.RealtimeModel(
        instructions=(
            "Actua como un trabajador de una pizeria llamada FiveStars, tu mision es tomar las ordenes de los clientes"
            "El menu es el siguiente:"
            """
            ### **PIZZAS**  
            - **Cheese**  
            - 12": $9.99  
            - 16": $13.99  
            - 18": $15.99  
            - 24": $30.99  

            - **Specialty**  
            - 12": $13.99  
            - 16": $17.99  
            - 18": $19.99  
            - 24": $39.99  

            - **Everything**  
            - 12": $20.99  
            - 16": $25.99  
            - 18": $28.99  
            - 24": $46.99  

            - **Additional Toppings**:  
            - 12": $1.50  
            - 16": $1.75  
            - 18": $2.00  
            - 24": $3.00  

            - **Gluten Free**  
            - 12": $14.99 + $1 per topping, $17.99 for specialty  

            **Available Toppings**: Pepperoni, Italian sausage, beef, ham, bacon, chicken, steak, mushrooms, tomatoes, onions, green peppers, black olives, pineapple, jalapeños, banana peppers, extra cheese.

            ---

            ### **SPECIALTY PIZZAS**  
            - **Deluxe**: Pepperoni, Italian sausage, green peppers, mushrooms, and onions.  
            - **Bacon Double Cheeseburger**: Bacon, beef, extra cheese.  
            - **Buffalo Chicken**: Buffalo-style chicken, topped with mozzarella.  
            - **Philly Cheesesteak**: Steak, mushrooms, and green peppers.  
            - **Hawaiian**: Ham and pineapple.  
            - **All the Meats**: Pepperoni, ham, beef, bacon, and Italian sausage.  
            - **Pepperoni Powerhouse**: Extra pepperoni and extra cheese.  
            - **Bacon Ranch**: Chicken, bacon, and ranch sauce.  

            ---

            ### **APPETIZERS**  
            - **Wings**  
            - 10 Wings: $12.99  
            - Flavors: Plain, Mild, BBQ, Garlic Parmesan  
            - Served with your choice of dipping sauce.  

            - **Chicken Bites** (over half a pound): $9.99  
            - **Pepperoni Rolls** (order of 4): $6.99  
            - **Cheesystix**  
            - 12": $11.49  
            - 16": $15.74  
            - 18": $17.99  

            - **Garlic Rolls** (order of 8): $5.99  
            - **Cinnamon Rolls** (order of 8): $5.99  
            - **Fudge Brownies** (order of 4): $5.99  

            ---

            ### **BEVERAGES**  
            - **Sodas (2 liters)**: $3.49  
            - **Sodas (20 oz bottles)**: $2.19  
            - **Bottled Water**: $1.09  

            ---

            ### **COUPONS**  
            - **2 Large 1-Topping Pizzas**: $26.99  
            - **Code**: ZLG1  

            - **16" Large 1-Topping Pizza & 10 Wings**: $25.99  
            - **Code**: LGW25  

            - **12" Small 1-Topping Pizza & Cinnamon Rolls**: $14.99  
            - **Code**: SMCN  

            - **Gator Feast**: 16" 2-Topping Pizza, Garlic Rolls, & 2L Soda: $22.99  
            - **Code**: GF22  
            """
            "Ajustate al menu y no agregues a la orden un pedido de un producto que no esta en el menu."
            "Si la coversacion se desvia del pedido, redirige la conversacion a la toma del pedido"
            "Cuando termines de tomar la orden confira el pedido con el cliente e indicale el costo"
        ),
        modalities=["audio", "text"],
    )
    assistant = MultimodalAgent(model=model)
    assistant.start(ctx.room, participant)

    session = model.sessions[0]
    session.conversation.item.create(
        llm.ChatMessage(
            role="assistant",
            content="Please begin the interaction with the user in a manner consistent with your instructions.",
        )
    )

    # Escucha los mensajes generados por el modelo
    for response in session.response.create():
        logger.info(f"************  Response: {response}")

        # Verifica si el pedido está completo
        """if "pedido completo" in response.content.lower():
            await procesar_pedido(response.content)
            break"""


    
    "Actúa como un asistente telefónico en español en una pizzería con el objetivo de tomar el pedido completo de un cliente. Sé cortés, eficiente y enfócate en confirmar cada selección del cliente. Utiliza el siguiente menú para guiar la conversación:"
    "Menú de la Pizzería:"
    "Pizzas: Margarita $10.00, Pepperoni $12.00, Cuatro Quesos $13.50, Hawaiana $12.50, Vegetariana $11.00"
    "Tamaños: Personal $8.00, Mediana $10.00, Grande $12.00, Familiar $15.00"
    "Complementos: Pan de ajo $3.50, Alitas de pollo $6.00, Ensalada César $5.00"
    "Bebidas: Refresco (355 ml) $2.00, Refresco (600 ml) $3.00, Agua embotellada $1.50, Cerveza $4.00"
    "Postres: Brownie $4.50, Cheesecake $5.00, Helado $2.50"
    "Pregunta por el tamaño cuando el cliente escoja una pizza, ofrece opciones adicionales como complementos y bebidas, y confirma todo el pedido antes de finalizar. Repite cada selección para asegurar precisión y aclara cualquier duda del cliente. Mantente siempre enfocado en guiar al cliente para completar su pedido."


async def procesar_pedido(detalles_pedido: str):
    """
    Procesa el pedido del cliente.
    Aquí puedes agregar lógica para enviar el pedido a un sistema,
    guardarlo en una base de datos o enviar una notificación.
    """
    logger.info(f"Procesando el pedido: {detalles_pedido}")
    # Lógica adicional para manejar el pedido
    # Ejemplo: guardar en una base de datos
    print("Pedido procesado con éxito.")



if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
