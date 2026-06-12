import discord
from discord.ext import commands
from discord.ui import Button, View
from gpiozero import OutputDevice
from dotenv import load_dotenv
import os
import time

# Pin Configuration
# Use OutputDevice for relays instead of LED to handle active_high/active_low logic properly.
# Many 5V relays for Arduino/Raspberry Pi trigger on LOW signals. 
# If your relay turns ON when the Pi boots, change `active_high=True` to `active_high=False`.
RELAY_PIN = 17 
relay = OutputDevice(RELAY_PIN, active_high=True, initial_value=False)

class LightControlView(View):
    def __init__(self):
        super().__init__(timeout=None) # timeout=None makes the view persistent across restarts
        self.last_toggled = 0.0
        self.cooldown = 2.0 # 2 seconds cooldown to prevent relay chatter

    # custom_id is REQUIRED for persistent views
    @discord.ui.button(label="Toggle Light", style=discord.ButtonStyle.primary, custom_id="toggle_light_btn")
    async def toggle_button(self, interaction: discord.Interaction, button: Button):
        current_time = time.time()
        
        # Debounce / Cooldown check
        if current_time - self.last_toggled < self.cooldown:
            await interaction.response.send_message("Please wait a moment before toggling again to protect the relay.", ephemeral=True)
            return
            
        self.last_toggled = current_time

        # Toggle the relay state physically
        relay.toggle()
        
        # Determine the new state for the UI
        is_on = relay.is_active
        state_text = "ON" if is_on else "OFF"
        
        # Update button color based on state (Green for ON, Gray for OFF)
        button.style = discord.ButtonStyle.success if is_on else discord.ButtonStyle.secondary
        
        # Edit the message with the new state
        await interaction.response.edit_message(content=f"The light is currently **{state_text}**.", view=self)

class LightBot(commands.Bot):
    def __init__(self):
        # Intents dictate what events the bot receives
        intents = discord.Intents.default()
        intents.message_content = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # We must register the persistent view on startup so it handles clicks 
        # on messages sent before the bot restarted.
        self.add_view(LightControlView())

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print(f'Ready to toggle relay on GPIO {RELAY_PIN}!')
        print('------')

bot = LightBot()

@bot.command()
@commands.is_owner() # Only the user who created the application in Discord can use this command
async def spawn(ctx):
    """Spawns the light control dashboard."""
    view = LightControlView()
    await ctx.send("The light is currently **OFF**.", view=view)

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the token from an environment variable for security
    TOKEN = os.environ.get("DISCORD_TOKEN")
    
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN environment variable not set.")
        print("Please create a .env file and add: DISCORD_TOKEN=your_token_here")
        exit(1)
        
    bot.run(TOKEN)
