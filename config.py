import os
import requests
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

users = {}

# Сохраняем состояние пользователя
class Form(StatesGroup):
    weight = State()
    height = State() 
    age = State()
    activity = State()
    city = State()
    calorie_custom = State()
    food_amount = State()

# Функция для получения температуры
def get_temperature(city_name):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=3)
        data = response.json()
        
        if response.status_code != 200:
            return None

        temperature = data["main"]["temp"]
        return round(temperature, 1)
    except:
        return None

# Функции расчета нормы воды
def calculate_water_goal(weight_kg, activity_min, temperature=None):
    base_water = weight_kg * 30
    activity_water = (activity_min // 30) * 500
    temp_water = 0
    if temperature is not None and temperature > 25:
        temp_water = 500
   
    total_water = base_water + activity_water + temp_water
    return int(total_water)

# Функции расчета нормы еды
def calculate_calorie_goal(weight_kg, height_cm, age_years, activity_min):
    cal_base = 10 * weight_kg + 6.25 * height_cm - 5 * age_years
    
    if activity_min < 30:
        workout_norm = 0
    elif activity_min < 60:
        workout_norm = 200
    elif activity_min < 90:
        workout_norm = 300
    else:
        workout_norm = 400
    
    
    total_calories = cal_base + workout_norm
    return int(total_calories)


# Функция для получения калорийности продукта
def get_food_info(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        if products:
            first_product = products[0]
            return {
                'name': first_product.get('product_name', 'Неизвестно'),
                'calories': first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
            }
        return None
    print(f"Ошибка: {response.status_code}")
    return None

workout_cal = {
    "бег": 600,        
    "ходьба": 300,    
    "велосипед": 500,  
    "плавание": 550,   
    "йога": 250,       
    "зал": 400,
    "танцы": 350
}