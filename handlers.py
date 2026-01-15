from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import matplotlib.pyplot as plt
from aiogram.types import BufferedInputFile
import io
import random

from config import users, Form, calculate_water_goal, calculate_calorie_goal, get_temperature, get_food_info, workout_cal


router = Router()

# === ОСНОВНЫЕ КОМАНДЫ ===

@router.message(Command("start"))
async def start_command(message: types.Message):
    user_id = str(message.from_user.id)
    
    if user_id not in users:
        users[user_id] = {}
        await message.answer(
            "Привет! Я бот для отслеживания воды, калорий и активности.\n\n"
            "Сначала настрой свой профиль командой /set_profile"
        )
    else:
        await message.answer("С возвращением!")

@router.message(Command("help"))
async def help_command(message: types.Message):
    help_text = """
📋 Доступные команды:

/set_profile - Настроить профиль
/norms - Показать ваши нормы
/set_calories - Изменить цель калорий вручную
/log_water <количество> - Записать воду (мл)
/log_food <название> - Записать еду
/log_workout <тип> <время> - Записать тренировку
/workouts - Показать типы тренировок
/check_progress - Показать прогресс
/graphs - Круговые диаграммы прогресса
/reset - Сбросить дневные данные

"""
    await message.answer(help_text)



@router.message(Command("norms"))
async def show_norms(message: types.Message):
    user_id = str(message.from_user.id)
    
    if user_id not in users or not users[user_id]:
        await message.answer("Сначала настройте профиль: /set_profile")
        return
    
    user_data = users[user_id]
    
    response = (
        f"Ваши дневные нормы:\n\n"
        f"Вода: {user_data.get('water_goal', 0)} мл\n"
        f"Калории: {user_data.get('calorie_goal', 0)} ккал\n\n"
        f"Ваши данные:\n"
        f"• Вес: {user_data.get('weight')} кг\n"
        f"• Рост: {user_data.get('height')} см\n"
        f"• Возраст: {user_data.get('age')} лет\n"
        f"• Активность: {user_data.get('activity')} мин/день\n"
        f"• Город: {user_data.get('city')}"
    )
    
    await message.answer(response)

# === ПРОФИЛЬ ===

@router.message(Command("set_profile"))
async def set_profile_start(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш вес (в кг):")
    await state.set_state(Form.weight)

@router.message(Form.weight)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text)
        await state.update_data(weight=weight)
        await message.answer("Введите ваш рост (в см):")
        await state.set_state(Form.height)
    except:
        await message.answer("Введите число")

@router.message(Form.height)
async def process_height(message: types.Message, state: FSMContext):
    try:
        height = float(message.text)
        await state.update_data(height=height)
        await message.answer("Введите ваш возраст:")
        await state.set_state(Form.age)
    except:
        await message.answer("Введите число")

@router.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
        await state.update_data(age=age)
        await message.answer("Сколько минут активности у вас в день?")
        await state.set_state(Form.activity)
    except:
        await message.answer("Введите целое число")

@router.message(Form.activity)
async def process_activity(message: types.Message, state: FSMContext):
    try:
        activity = int(message.text)
        await state.update_data(activity=activity)
        await message.answer("В каком городе вы находитесь?")
        await state.set_state(Form.city)
    except:
        await message.answer("Введите целое число")

@router.message(Form.city)
async def process_city(message: types.Message, state: FSMContext):
    city = message.text
    
    user_data = await state.get_data()
    user_id = str(message.from_user.id)
    
    weight = user_data.get("weight")
    height = user_data.get("height")
    age = user_data.get("age")
    activity = user_data.get("activity")
    
    temperature = get_temperature(city)
    water_goal = calculate_water_goal(weight, activity, temperature)
    calorie_goal = calculate_calorie_goal(weight, height, age, activity)
    
    users[user_id] = {
        "weight": weight,
        "height": height,
        "age": age,
        "activity": activity,
        "city": city,
        "water_goal": water_goal,
        "calorie_goal": calorie_goal,
        "logged_water": 0,
        "logged_calories": 0,
        "burned_calories": 0
    }
    
    response = f"✅ Профиль сохранен!\n\n Ваши дневные нормы:\n Вода: {water_goal} мл\n Калории: {calorie_goal} ккал\n\n"
    
    if temperature is not None:
        response += f"Температура в {city}: {temperature}°C\n"
    
    response += "\nОсновные команды:\n/log_water - вода\n/log_food - еда\n/log_workout - тренировка\n/check_progress - прогресс\n/set_calories - задать норму калорий вручную"
    
    await message.answer(response)
    await state.clear()

# Настройка команды для задания нормы калорий вручную
@router.message(Command("set_calories"))
async def set_calories_command(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    
    if user_id not in users or not users[user_id]:
        await message.answer("Сначала настройте профиль: /set_profile")
        return
    
    await message.answer("Введите новую цель по калориям (например: 2000):")
    await state.set_state(Form.calorie_custom)

@router.message(Form.calorie_custom)
async def process_calorie_update(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    
    try:
        calorie_goal = int(message.text)
    except ValueError:
        await message.answer("Введите число:")
        return
    
    users[user_id]["calorie_goal"] = calorie_goal
    
    await message.answer(f"Цель калорий обновлена: {calorie_goal} ккал")
    await state.clear()

# === ВОДА ===

@router.message(Command("log_water"))
async def log_water(message: types.Message):
    user_id = str(message.from_user.id)
    
    if user_id not in users or not users[user_id]:
        await message.answer("Сначала настройте профиль: /set_profile")
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("Использование: /log_water <количество в мл>\nНапример: /log_water 500")
            return
        
        water_amount = int(args[1])
        if water_amount <= 0:
            await message.answer("Введите положительное число")
            return
        
        users[user_id]["logged_water"] += water_amount
        
        water_goal = users[user_id].get("water_goal", 0)
        logged_water = users[user_id].get("logged_water", 0)
        remaining = water_goal - logged_water
        
        if remaining > 0:
            await message.answer(
                f"Записано: {water_amount} мл воды\n\n"
                f"Всего выпито: {logged_water} мл\n"
                f"Норма: {water_goal} мл\n"
                f"Осталось: {remaining} мл"
            )
        else:
            await message.answer(
                f"Записано: {water_amount} мл воды\n\n"
                f"✅ Вы выполнили норму воды!\n"
                f"Выпито: {logged_water} мл из {water_goal} мл"
            )
            
    except ValueError:
        await message.answer("Пожалуйста, введите число")


# === ЕДА ===

@router.message(Command("log_food"))
async def log_food_start(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    
    if user_id not in users or not users[user_id]:
        await message.answer("Сначала настройте профиль: /set_profile")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /log_food <название продукта>\nПример: /log_food банан")
        return
    
    product_name = args[1]
    product_info = get_food_info(product_name)
    
    if not product_info:
        await message.answer(f"Продукт '{product_name}' не найден.\nПопробуйте ввести другое наименование")
        return
    
    await state.update_data(food_info=product_info)
    
    calories = product_info.get("calories", 0)
    await message.answer(
        f"Найден продукт: {product_info['name']}\n"
        f"На 100 г: {calories} ккал\n\n"
        f"Сколько грамм вы съели?"
    )
    
    await state.set_state(Form.food_amount)

@router.message(Form.food_amount)
async def process_food_amount(message: types.Message, state: FSMContext):
    try:
        grams = float(message.text)
        
        user_data = await state.get_data()
        food_info = user_data.get("food_info")
        user_id = str(message.from_user.id)
        
        calories_per_100g = food_info.get("calories", 0)
        total_calories = (calories_per_100g * grams) / 100
        
        users[user_id]["logged_calories"] += total_calories
        
        await message.answer(
            f"✅ Записано: {food_info['name']}\n"
            f"Порция: {grams} г\n"
            f"Калории: {total_calories:.1f} ккал\n\n"
            f"Всего потреблено: {users[user_id]['logged_calories']:.1f} ккал"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("Введите число:")

# === ТРЕНИРОВКИ ===

@router.message(Command("log_workout"))
async def log_workout(message: types.Message):
    user_id = str(message.from_user.id)
    
    if user_id not in users or not users[user_id]:
        await message.answer("Сначала настройте профиль: /set_profile")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Использование: /log_workout <тип> <минуты>\nПример: /log_workout бег 30")
        return
    
    workout_type = args[1].lower()
    
    try:
        minutes = int(args[2])

    except:
        await message.answer("Введите число минут")
        return
    
    if workout_type not in workout_cal:
        types = ", ".join(workout_cal.keys())
        await message.answer(f"Неизвестный тип тренировки. Доступно: {types}")
        return
    
    cals_per_hour = workout_cal[workout_type]
    burned_calories = (cals_per_hour * minutes) / 60
    extra_water = (minutes // 30) * 200
    
    users[user_id]["burned_calories"] += burned_calories
    
    response = (
        f"{workout_type.capitalize()} {minutes} минут - {burned_calories:.0f} ккал.\n"
        f"Дополнительно: выпейте {extra_water} мл воды."
    )
    # Не ясно по условию, должна ли норма воды увеличиваться на extra_water или это просто выводится текстом как рекомендация. Оставила второй вариант
    
    await message.answer(response)

@router.message(Command("workouts"))
async def show_workouts(message: types.Message):
    response = "Доступные тренировки:\n"
    for workout, calories in workout_cal.items():
        response += f"{workout}: {calories} ккал/час\n"
    response += "\nПример: /log_workout бег 30"
    await message.answer(response)

# === ПРОГРЕСС ===

@router.message(Command("check_progress"))
async def check_progress(message: types.Message):
    user_id = str(message.from_user.id)
    
    if user_id not in users or not users[user_id]:
        await message.answer("Сначала настройте профиль: /set_profile")
        return
    
    user_data = users[user_id]
    
    water_goal = user_data.get("water_goal", 0)
    logged_water = user_data.get("logged_water", 0)
    water_remaining = max(0, water_goal - logged_water)
    water_percentage = (logged_water / water_goal * 100) if water_goal > 0 else 0
    
    calorie_goal = user_data.get("calorie_goal", 0)
    # Полученные калории от приема пищи
    logged_calories = user_data.get("logged_calories", 0)
    # Сожженые калории от тренировок
    burned_calories = user_data.get("burned_calories", 0)
    
    cal_diff = logged_calories - burned_calories
    calories_remaining = calorie_goal - cal_diff
    
    # Создаю шкалу прогресса по еде и воде для наглядности (на мой взгляд, это лучше, чем график, но раз в задании просят, то ниже еще есть код для графика)
    def create_bar(percentage, width=10):
        filled = int((percentage / 100) * width)
        return "█" * filled + "░" * (width - filled)
    
    water_bar = create_bar(min(100, water_percentage))
    cal_percentage = (cal_diff / calorie_goal * 100) if calorie_goal > 0 else 0
    cal_percentage = max(0, min(100, cal_percentage))
    calorie_bar = create_bar(cal_percentage)
    
    response = (
        "📊 Прогресс:\n\n"
        
        "Вода:\n"
        f"Прогресс: [{water_bar}] {min(100, water_percentage):.0f}%\n"
        f"Выпито: {logged_water} мл из {water_goal} мл\n"
        f"Осталось: {water_remaining} мл\n\n"
        
        "Калории:\n"
        f"Прогресс: [{calorie_bar}] {min(100, (cal_diff / calorie_goal * 100) if calorie_goal > 0 else 0):.0f}%\n"
        f"Потреблено: {logged_calories:.0f} ккал\n"
        f"Сожжено тренировками: {burned_calories:.0f} ккал\n"
        f"Баланс: {cal_diff:.0f} ккал\n"
        f"Норма: {calorie_goal} ккал\n"
        f"Осталось: {calories_remaining:.0f} ккал\n\n"
    )
    
    # Также на бонусные баллы добавляю логику по рекомендациям пользователю
    recommendations = []
    if water_remaining > 500:
        recommendations.append(f"Выпейте еще хотя бы бутылку воды сегодня")
    elif water_remaining > 300:
        recommendations.append(f"Выпейте еще стакан воды сегодня")
    elif water_remaining > 0:
        recommendations.append(f"Вы почти у цели! Выпейте еще {water_remaining} мл")
    elif water_remaining <= 0:
        recommendations.append(f"Вы уже выполнили норму воды!")

    if calories_remaining >= 0:
        recommendations.append(f"Можно съесть еще {calories_remaining:.0f} ккал")
    elif -250 <= calories_remaining < 0:
        exercise = random.choice(list(workout_cal.keys()))
        recommendations.append(f"Вы превысили дневную норму калорий! {exercise.capitalize()} в течение 30 минут сожжет {workout_cal[exercise] // 2:.0f}")
    elif calories_remaining < -250:
        exercise = random.choice(list(workout_cal.keys()))
        recommendations.append(f"Вы превысили дневную норму калорий! {exercise.capitalize()} в течение 60 минут сожжет {workout_cal[exercise]:.0f}")

    
    
    if recommendations:
        response += "💡 Рекомендации:\n" + "\n".join(recommendations)
    
    await message.answer(response)

# === СБРОС ДАННЫХ ===
# Также добавила команду, которая сбрасывает прогресс по воде, еде и тренировкам (в идеале лучше, чтобы это происходило автоматически раз в сутки, но пока так)
@router.message(Command("reset"))
async def reset_command(message: types.Message):
    user_id = str(message.from_user.id)
    
    if user_id not in users:
        await message.answer("Сначала настройте профиль: /set_profile")
        return
    
    users[user_id]["logged_water"] = 0
    users[user_id]["logged_calories"] = 0
    users[user_id]["burned_calories"] = 0
    
    await message.answer("✅ Дневные данные сброшены")

# === ГРАФИКИ ===
@router.message(Command("graphs"))
async def pie_chart(message: types.Message):

    user_id = str(message.from_user.id)
    
    if user_id not in users or not users[user_id]:
        await message.answer("Сначала настройте профиль: /set_profile")
        return
    
    data = users[user_id]
    
    # Вода
    water_drunk = data.get("logged_water", 0)
    water_goal = data.get("water_goal", 1)
    water_left = max(0, water_goal - water_drunk)
    
    # Калории  
    calories_eaten = data.get("logged_calories", 0)
    burned_calories = data.get("burned_calories", 0)
    calorie_goal = data.get("calorie_goal", 1)
    cal_diff = calories_eaten - burned_calories
    calories_left = max(0, calorie_goal - cal_diff)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    
    ax1.pie([water_drunk, water_left], labels=['Выпито', 'Осталось'], autopct='%1.0f%%')
    ax1.set_title('Вода')
    
    ax2.pie([cal_diff, calories_left], labels=['Баланс', 'Осталось'], autopct='%1.0f%%')
    ax2.set_title('Калории')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    caption = f"Вода: {water_drunk}/{water_goal} мл\nКалории: {calories_eaten}/{calorie_goal} ккал"
    
    photo = BufferedInputFile(buf.getvalue(), filename="graph.png")
    
    await message.answer_photo(photo, caption=caption)