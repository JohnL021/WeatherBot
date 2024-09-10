import os
import discord
from discord.ext import commands
from discord import app_commands
import requests
from dotenv import load_dotenv
from discord.ext import tasks

# Load environment variables from .env file
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID'))

# Debug prints to verify environment variables
print(f'DISCORD_TOKEN: {DISCORD_TOKEN}')
print(f'WEATHER_API_KEY: {WEATHER_API_KEY}')
print(f'CHANNEL_ID: {CHANNEL_ID}')
print(f'BOT_OWNER_ID: {BOT_OWNER_ID}')

# Create an intents object
intents = discord.Intents.default()
intents.messages = True  # Enable the message intent

# Initialize bot with commands extension
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("Bot is online!")
    await bot.tree.sync()  # Sync the slash commands with Discord
    daily_weather_alert.start()  # Start the daily alert loop

@bot.tree.command(name="weather", description="Get the weather for a specified city")
async def weather(interaction: discord.Interaction, city: str):
    weather = get_weather(city)
    if weather:
        await interaction.response.send_message(embed=weather)
    else:
        await interaction.response.send_message(f"Sorry, I couldn't find the weather for {city}.")
        
@bot.tree.command(name="forecast", description="Get a 3-day weather forecast for a specified city")
async def forecast(interaction: discord.Interaction, city: str):
    #print(f"Forecast command received for city: {city}")
    forecast = get_forecast(city)
    if forecast:
        await interaction.response.send_message(embed=forecast)
    else:
        await interaction.response.send_message(f"Sorry, I couldn't find the forecast for {city}.")

@bot.tree.command(name='airquality', description="Get the air quality for a specific city.")
async def airquality(interaction: discord.Interaction, city: str):
    air_quality = get_air_quality(city)
    if air_quality:
        await interaction.response.send_message(embed=air_quality)
    else:
        await interaction.response.send_message(f"Sorry, I couldn't find the air quality data for {city}.")
        
@bot.tree.command(name="getrecommendation_f", description="Get the clothes recommendation for specific weather conditions. (Fahrenheit)")
async def getrecommendation_f(interaction: discord.Interaction, description: str, degree: float):
    recom = get_clothing_recommendation(description, degree)
    if recom:
        await interaction.response.send_message(f"{recom}")
    else:
        await interaction.response.send_message(f"Sorry, I couldn't find the recommendation.")
        
@bot.tree.command(name="getrecommendation_c", description="Get the clothes recommendation for specific weather conditions. (Celsius)")
async def getrecommendation_c(interaction: discord.Interaction, description: str, degree: float):
    faren = (degree * (9 / 5)) + 32
    recom = get_clothing_recommendation(description, faren)
    if recom:
        await interaction.response.send_message(f"{recom}")
    else:
        await interaction.response.send_message(f"Sorry, I couldn't find the recommendation.")
    
@bot.tree.command(name="shutdown", description="Shutdown the bot")
async def shutdown(interaction: discord.Interaction):
    if interaction.user.id == BOT_OWNER_ID:
        await interaction.response.send_message("Shutting down...")
        await bot.close()
    else:
        await interaction.response.send_message("You do not have permission to use this command.")
        
@bot.tree.command(name="f_to_c", description="Convert from °F to °C")
async def f_to_c(interaction: discord.Interaction, degree: float):
    celsius = (degree - 32) * 5 / 9
    await interaction.response.send_message(f"The degree in Celsius is {celsius:.2f}°C.")
    
@bot.tree.command(name="c_to_f", description="Convert from °C to °F")
async def c_to_f(interaction: discord.Interaction, degree: float):
    fahrenheit = (degree * (9 / 5)) + 32
    await interaction.response.send_message(f"The degree in Fahrenheit is {fahrenheit:.2f}°F.")

def get_weather(city):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': WEATHER_API_KEY,
        'units': 'imperial'
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        weather_desc = data['weather'][0]['description'].capitalize()
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        city_name = data['name']
        recommendation = get_clothing_recommendation(weather_desc, temp)
        
        weather_images = {
            'Clear': 'https://images.pexels.com/photos/96622/pexels-photo-96622.jpeg',
            'Clouds': 'https://images.pexels.com/photos/53594/blue-clouds-day-fluffy-53594.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1',
            'Rain': 'https://images.pexels.com/photos/39811/pexels-photo-39811.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1',
            'Thunderstorm': 'https://images.pexels.com/photos/1114688/pexels-photo-1114688.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1',
            'Snow': 'https://images.pexels.com/photos/688660/pexels-photo-688660.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1',
            'Drizzle': 'https://images.pexels.com/photos/7002970/pexels-photo-7002970.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1',
            'Mist': 'https://images.pexels.com/photos/163323/fog-dawn-landscape-morgenstimmung-163323.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1',
            'Fog': 'https://images.pexels.com/photos/1605325/pexels-photo-1605325.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1',
            'Haze': 'https://images.pexels.com/photos/1165991/pexels-photo-1165991.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1'
            
        }
        
        weather_main = data['weather'][0]['main']
        image_url = weather_images.get(weather_main, 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg')
        
        embed = discord.Embed(
            title=f"Weather in {city_name}",
            description=f"{weather_desc}\nTemperature: {temp}°F\nHumidity: {humidity}%\nWind Speed: {wind_speed} mph\n\n{recommendation}",
            color=discord.Color.blue()
        )
        embed.set_image(url=image_url)
        return embed
    else:
        return None
    
def get_forecast(city):
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        'q': city,
        'appid': WEATHER_API_KEY,
        'units': 'imperial',  # Imperial units
        'cnt': 3 * 8  # 3 days of data
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        forecast_list = data['list']
        city_name = data['city']['name']
        
        embed = discord.Embed(
            title=f"3-Day Weather Forecast for {city_name}",
            color=discord.Color.blue()
        )
        
        for forecast in forecast_list:
            dt_txt = forecast['dt_txt']
            weather_desc = forecast['weather'][0]['description'].capitalize()
            temp = forecast['main']['temp']
            humidity = forecast['main']['humidity']
            wind_speed = forecast['wind']['speed']

            embed.add_field(
                name=dt_txt,
                value=f"{weather_desc}\nTemperature: {temp}°F\nHumidity: {humidity}%\nWind Speed: {wind_speed} mph",
                inline=False
            )

        return embed
    else:
        return None
    
def get_air_quality(city):
    geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
    air_quality_url = "http://api.openweathermap.org/data/2.5/air_pollution"
    
    # Get latitude and longitude for the city
    geocode_params = {
        'q': city,
        'appid': WEATHER_API_KEY,
        'limit': 1
    }
    
    geocode_response = requests.get(geocode_url, params=geocode_params)
    if geocode_response.status_code == 200:
        geocode_data = geocode_response.json()
        if len(geocode_data) > 0:
            lat = geocode_data[0]['lat']
            lon = geocode_data[0]['lon']

            # Fetch air quality data
            air_quality_params = {
                'lat': lat,
                'lon': lon,
                'appid': WEATHER_API_KEY
            }
            air_quality_response = requests.get(air_quality_url, params=air_quality_params)
            if air_quality_response.status_code == 200:
                data = air_quality_response.json()
                aqi = data['list'][0]['main']['aqi']

                # AQI Categories based on the AQI value
                aqi_description = {
                    1: "Good",
                    2: "Fair",
                    3: "Moderate",
                    4: "Poor",
                    5: "Very Poor"
                }

                description = aqi_description.get(aqi, "Unknown")
                embed = discord.Embed(
                    title=f"Air Quality in {city}",
                    description=f"AQI: {aqi} ({description})",
                    color=discord.Color.green() if aqi == 1 else discord.Color.red()
                )
                return embed

    return None
    
def get_clothing_recommendation(weather_desc, temp):
    if 'rain' in weather_desc.lower() or 'drizzle' in weather_desc.lower():
        if temp > 60:
            return "Recommendation: Wear a light raincoat and waterproof shoes!"
        else:
            return "Recommendation: Wear a warm raincoat, waterproof shoes, and some layers of clothing!"
    if 'snow' in weather_desc.lower():
        return "Recommendation: Wear a heavy coat, gloves, scarf, and warm boots!"
    if 'clear' in weather_desc.lower() or 'sun' in weather_desc.lower():
        if temp > 85:
            return "Recommendation: Wear light clothing, sunglasses, and stay hydrated!"
        elif temp > 60:
            return "Recommendation: Wear comfortable clothing, and enjoy the nice weather outside!"
        else:
            return "Recommendation: Wear a jacket and some layers of clothes!"
    if 'cloud' in weather_desc.lower() or 'overcast' in weather_desc.lower():
        if temp > 70:
            return "Recommendation: Wear light layers, and carry a jacket just in case!"
        else:
            return "Recommendation: Wear a warm jacket, and some layers of clothing!"
    if temp < 32:
        return "Recommendation: Wear a heavy coat, hat, scarf, and gloves!"
    return "Recommendation: However you want!"

@tasks.loop(hours=24)
async def daily_weather_alert():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        city = "Fairfax"  # Replace with the city you want alerts for
        weather = get_weather(city)
        if weather:
            await channel.send(embed=weather)
            
if DISCORD_TOKEN is None or CHANNEL_ID is None or BOT_OWNER_ID is None:
    raise ValueError("DISCORD_TOKEN, CHANNEL_ID, or BOT_OWNER_ID is not set. Please check your .env file.")

bot.run(DISCORD_TOKEN)