import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random

# Constants
TOKEN = "MTQwMzU0OTc2MzQzNzA2ODMzOQ.GLXt9i.gUuUQTFUOx2zI2Kxr9pHbM5mcYtva7qi1SwpWM"  # Besser in Umgebungsvariablen speichern
CREDITS_FILE = "credits.json"
ACCOUNT_TYPES = ["unbanned", "banned", "netflix", "spotify"]  # Angepasst zu deinen neuen Typen
RESTOCK_CHANNEL_ID = 1417176018178801757  # Deine Kanal-ID

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True  # Aktiviere message_content Intent, falls benötigt
bot = commands.Bot(command_prefix="!", intents=intents)

# Utility functions
def load_credits():
    if not os.path.exists(CREDITS_FILE):
        return {}
    try:
        with open(CREDITS_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        return {}

def save_credits(credits):
    with open(CREDITS_FILE, "w") as f:
        json.dump(credits, f)

def get_stock():
    stock = {}
    for acc_type in ACCOUNT_TYPES:
        filename = f"accounts_{acc_type}.txt"
        if not os.path.exists(filename):
            stock[acc_type] = 0
        else:
            with open(filename, "r") as f:
                stock[acc_type] = len([line for line in f if line.strip()])
    return stock

def get_account(account_type):
    filename = f"accounts_{account_type}.txt"
    if not os.path.exists(filename):
        return None
    with open(filename, "r") as f:
        lines = f.readlines()
    if not lines:
        return None
    account = lines[0].strip()
    with open(filename, "w") as f:
        f.writelines(lines[1:])
    return account

def add_account(account_type, account_data):
    """Fügt einen Account zu einer Datei hinzu und gibt True zurück, wenn erfolgreich."""
    if account_type not in ACCOUNT_TYPES:
        return False
    filename = f"accounts_{account_type}.txt"
    try:
        with open(filename, "a") as f:
            f.write(account_data + "\n")
        return True
    except Exception as e:
        print(f"Fehler beim Hinzufügen des Accounts zu {filename}: {e}")
        return False

# Bot commands
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="stock", description="Show stock for all account types.")
async def stock_cmd(interaction: discord.Interaction):
    stock = get_stock()
    msg = "**Account Stock:**\n"
    for acc_type, count in stock.items():
        msg += f"{acc_type.capitalize()}: {count}\n"
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="gamble", description="Gamble your credits (50/50 chance).")
@app_commands.describe(amount="Amount of credits to gamble")
async def gamble_cmd(interaction: discord.Interaction, amount: int):
    user_id = str(interaction.user.id)
    credits = load_credits()
    user_credits = credits.get(user_id, 0)
    if amount <= 0:
        await interaction.response.send_message("Amount must be positive!", ephemeral=True)
        return
    if user_credits < amount:
        await interaction.response.send_message(f"Not enough credits! You have {user_credits}.", ephemeral=True)
        return
    if random.random() < 0.5:
        credits[user_id] -= amount
        save_credits(credits)
        await interaction.response.send_message(f"You lost {amount} credits! Remaining: {credits[user_id]}", ephemeral=True)
    else:
        credits[user_id] += amount
        save_credits(credits)
        await interaction.response.send_message(f"You won {amount} credits! Total: {credits[user_id]}", ephemeral=True)

@bot.tree.command(name="slots", description="Play the slot machine!")
@app_commands.describe(amount="Amount of credits to bet")
async def slots_cmd(interaction: discord.Interaction, amount: int):
    user_id = str(interaction.user.id)
    credits = load_credits()
    user_credits = credits.get(user_id, 0)
    if amount <= 0:
        await interaction.response.send_message("Amount must be positive!", ephemeral=True)
        return
    if user_credits < amount:
        await interaction.response.send_message(f"Not enough credits! You have {user_credits}.", ephemeral=True)
        return
    symbols = ["🍒", "🍋", "🔔", "⭐", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    win = False
    payout = 0
    if result[0] == result[1] == result[2]:
        win = True
        payout = amount * 5
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win = True
        payout = amount * 2
    if win:
        credits[user_id] += payout - amount
        save_credits(credits)
        await interaction.response.send_message(f"{' '.join(result)}\nYou won {payout} credits! Total: {credits[user_id]}", ephemeral=True)
    else:
        credits[user_id] -= amount
        save_credits(credits)
        await interaction.response.send_message(f"{' '.join(result)}\nYou lost {amount} credits! Remaining: {credits[user_id]}", ephemeral=True)

@bot.tree.command(name="purchase", description="Purchase an account with credits.")
@app_commands.describe(account_type="Type of account to purchase")
@app_commands.choices(account_type=[app_commands.Choice(name=acc_type.capitalize(), value=acc_type) for acc_type in ACCOUNT_TYPES])
async def purchase(interaction: discord.Interaction, account_type: app_commands.Choice[str]):
    user_id = str(interaction.user.id)
    credits = load_credits()
    user_credits = credits.get(user_id, 0)
    price = 10  # Price per account in credits
    if user_credits < price:
        await interaction.response.send_message(f"Not enough credits! (Required: {price}, You have: {user_credits})", ephemeral=True)
        return
    account = get_account(account_type.value)
    if not account:
        await interaction.response.send_message(f"No more {account_type.value} accounts available!", ephemeral=True)
        return
    credits[user_id] = user_credits - price
    save_credits(credits)
    await interaction.response.send_message(f"Here is your {account_type.value} account: `{account}`. Remaining credits: {credits[user_id]}", ephemeral=True)

@bot.tree.command(name="freeaccount", description="Get a Hypixel banned account.")
@app_commands.describe(account_type="Type of account to get (free)")
@app_commands.choices(account_type=[app_commands.Choice(name="Banned", value="banned")])
@app_commands.checks.cooldown(1, 3600)  # 1 Nutzung pro Stunde
async def freeaccount(interaction: discord.Interaction, account_type: app_commands.Choice[str]):
    if account_type.value != "banned":
        await interaction.response.send_message("Only banned accounts can be obtained with this command!", ephemeral=True)
        return
    account = get_account(account_type.value)
    if not account:
        await interaction.response.send_message("No banned accounts available!", ephemeral=True)
        return
    await interaction.response.send_message(f"Here is your free {account_type.value} account: `{account}`", ephemeral=True)

@bot.tree.command(name="credits", description="Show your current credits.")
async def credits_cmd(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    credits = load_credits()
    user_credits = credits.get(user_id, 0)
    await interaction.response.send_message(f"You have {user_credits} credits.", ephemeral=True)

@bot.tree.command(name="addcredits", description="Add credits to a user (Admin only).")
@app_commands.describe(user="User", amount="Amount of credits")
async def addcredits(interaction: discord.Interaction, user: discord.User, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only admins can add credits!", ephemeral=True)
        return
    credits = load_credits()
    user_id = str(user.id)
    credits[user_id] = credits.get(user_id, 0) + amount
    save_credits(credits)
    await interaction.response.send_message(f"Added {amount} credits to {user.mention}.", ephemeral=True)

@bot.tree.command(name="restock", description="Restock an account (Admin only).")
@app_commands.describe(
    account_type="Type of account to restock",
    account_data="Account details to add (e.g., username:password)"
)
@app_commands.choices(account_type=[app_commands.Choice(name=acc_type.capitalize(), value=acc_type) for acc_type in ACCOUNT_TYPES])
async def restock(interaction: discord.Interaction, account_type: app_commands.Choice[str], account_data: str):
    # Defer die Interaktion früh, um Acknowledgement-Probleme zu vermeiden
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send("Only admins can restock accounts!", ephemeral=True)
        return
    if not account_data.strip():
        await interaction.followup.send("Account data cannot be empty!", ephemeral=True)
        return
    if add_account(account_type.value, account_data):
        # Send restock message to the specified channel
        channel = bot.get_channel(RESTOCK_CHANNEL_ID)
        if channel:
            await channel.send(f"**Restock Alert!** A new {account_type.value.capitalize()} account has been added to the stock!")
        await interaction.followup.send(f"Successfully restocked {account_type.value} account: `{account_data}`", ephemeral=True)
    else:
        await interaction.followup.send(f"Failed to restock {account_type.value} account. Invalid account type or error occurred.", ephemeral=True)

# Fehlerhandler für Cooldown
@bot.tree.error
async def on_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        # Für Cooldown: Verwende followup, falls möglich (nach Defer), oder response falls nicht
        if interaction.response.is_done():
            # Wenn schon acknowledged, ignoriere oder logge
            print(f"Cooldown error for {interaction.user}: {error}")
        else:
            await interaction.response.send_message(f"Dieser Befehl hat einen Cooldown! Versuche es erneut in {int(error.retry_after)} Sekunden.", ephemeral=True)
    else:
        raise error

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)
