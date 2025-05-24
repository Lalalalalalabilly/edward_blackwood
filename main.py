import os
import discord
from discord.ext import commands
from flask import Flask # Pour le petit serveur web pour Render
from threading import Thread # Pour exécuter le serveur web en arrière-plan

# --- Partie Serveur Web pour Render ---
app = Flask(__name__)
PORT = int(os.environ.get('PORT', 5000)) # Render fournira cette variable

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
# --- Fin Partie Serveur Web ---

# --- Partie Bot Discord ---
# Récupérez le token Discord depuis les variables d'environnement (important pour la sécurité)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if DISCORD_TOKEN is None:
    print("Erreur : Le token Discord n'est pas configuré. Assurez-vous que la variable d'environnement DISCORD_TOKEN est définie.")
    exit()

# Définir les "intents" nécessaires (permissions pour votre bot)
# Pour un bot simple qui lit les messages et répond, les intents par défaut ne suffisent pas toujours.
# Il faut activer MESSAGE_CONTENT Intent dans le Developer Portal
intents = discord.Intents.default()
intents.message_content = True # Nécessaire pour lire le contenu des messages
intents.members = True # Optionnel, si vous voulez des infos sur les membres

# Créez une instance du bot
# Le préfixe de commande est ce qui doit être tapé avant la commande (ex: !ping)
bot = commands.Bot(command_prefix='!', intents=intents)

# Événement : Quand le bot est prêt et connecté
@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user.name} ({bot.user.id})')
    print('Le bot est en ligne !')
    # Lance le serveur web pour maintenir le bot actif sur Render
    keep_alive()

# Commande : !ping
@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong !')

# Événement : Quand un message est envoyé
@bot.event
async def on_message(message):
    # Ignore les messages du bot lui-même pour éviter les boucles infinies
    if message.author == bot.user:
        return

    # Traite les commandes (nécessaire pour que bot.command fonctionne)
    await bot.process_commands(message)

# Lance le bot Discord
# bot.run(DISCORD_TOKEN)
# Si vous voulez tester sur votre PC avant Render, vous pouvez décommenter la ligne ci-dessus
# et commenter la ligne bot.run(DISCORD_TOKEN) ci-dessous si vous utilisez keep_alive().
# Pour Render, le Flask server va gérer le lancement du bot.
# Pour un bot qui utilise un serveur web pour rester actif, il faut s'assurer que le bot démarre aussi
# La manière la plus simple est de s'assurer que `bot.run` est appelé après le démarrage du serveur Flask,
# mais Flask bloque l'exécution, donc on lance le bot dans un thread séparé.
# Plus simple: lancez le bot directement et comptez sur Render pour le maintenir actif.
# Pour les bots sur Render, il est plus commun d'avoir le bot en tant que "Background Worker" (payant)
# ou d'utiliser le Web Service *avec* un ping externe qui maintient l'application Python en vie,
# et le bot est juste une partie de cette application qui tourne.

# Relançons la logique de démarrage pour Render
# Si le bot est un Web Service, il doit démarrer le serveur web et le bot.
# Le moyen le plus simple est de démarrer Flask puis de démarrer le bot dans un thread.
# Cependant, discord.py `bot.run()` bloque l'exécution.
# Pour un Web Service sur Render, le mieux est que le point d'entrée HTTP démarre le bot en arrière-plan.

# Version simplifiée pour Render Web Service:
# Flask démarre, et le bot démarre en même temps.
# Le bot.run() devrait être lancé dans un thread séparé pour ne pas bloquer Flask.
# Mais discord.py gère le bouclage asynchrone déjà.
# Le code ci-dessus est pour une approche classique.

# Pour que cela fonctionne sur Render (Web Service gratuit), la structure est :
# Le script démarre le serveur Flask, et dans le même script, le bot se connecte.
# Le Flask server sert juste de "répondeur" pour Render.
# Le bot lui-même continuera de fonctionner.

# Pour un "Web Service" sur Render, le démarrage est un peu délicat avec discord.py et Flask.
# Voici une approche plus simple : le bot tourne, et le serveur Flask est juste une partie de l'application.
# Nous allons lancer le bot directement, et le serveur Flask sera géré par gunicorn/uvicorn sur Render.

# Code corrigé pour un démarrage plus simple sur Render Web Service :
# N'appelez PAS app.run() directement ici. Render utilisera Gunicorn/Uvicorn.
# L'important est que `bot.run(DISCORD_TOKEN)` soit appelé.

# Assurez-vous que le bot démarre même si le serveur web ne reçoit pas de requêtes constamment.
# La logique `keep_alive` est utile si vous avez un serveur HTTP séparé.
# Ici, nous voulons simplement que le bot se connecte et reste en ligne.

# Pour Render, votre "Start Command" sera `gunicorn main:app` ou `python main.py`
# Si vous utilisez `python main.py` comme commande de démarrage, le code ci-dessous sera exécuté.

# Le moyen le plus simple est de ne PAS utiliser Flask pour la gratuité de Render.
# Mais si on veut la gratuité de Render, il faut que le bot réponde à une requête HTTP.

# Ok, re-simplifions pour Render Web Service + UptimeRobot :
# Le code Flask doit s'exécuter dans un thread séparé pour ne pas bloquer le bot Discord.

try:
    # Lancer le serveur Flask dans un thread séparé
    keep_alive()
    # Lancer le bot Discord
    bot.run(DISCORD_TOKEN)
except discord.errors.LoginFailure:
    print("Échec de connexion : Le token Discord est invalide. Vérifiez votre variable d'environnement DISCORD_TOKEN.")
except Exception as e:
    print(f"Une erreur inattendue est survenue : {e}")
