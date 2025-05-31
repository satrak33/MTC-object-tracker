import pydirectinput
import math


# Рекомендація: pydirectinput може вимагати прав адміністратора для коректної роботи в деяких іграх.
# Встановлення: pip install pydirectinput

def target_mouse(target_roi: tuple[int, int, int, int],
                 screen_center: tuple[int, int],
                 dead_zone: int = 5,
                 move_speed: float = 0.15) -> None:
    """
    Плавно переміщує курсор миші до центру вказаного регіону (ROI).

    Працює подібно до прицілювання в FPS, де 'screen_center' є поточною позицією прицілу.

    Args:
        target_roi (tuple[int, int, int, int]): Координати цільової області
                                                  у форматі (x, y, ширина, висота).
        screen_center (tuple[int, int]): Координати центру екрана (поточного прицілу)
                                           у форматі (cx, cy).
        dead_zone (int, optional): Мінімальне зміщення (в пікселях) для активації руху.
                                   Запобігає тремтінню при малих відхиленнях. Defaults to 5.
        move_speed (float, optional): Коефіцієнт швидкості руху (від 0.0 до 1.0).
                                     Визначає, яку частку відстані до цілі миша
                                     пройде за один крок. Defaults to 0.15.
                                     Менші значення = плавніший, але повільніший рух.
    """
    roi_x, roi_y, roi_w, roi_h = target_roi
    screen_cx, screen_cy = screen_center

    # 1. Обчислити центр ROI
    target_center_x = roi_x + roi_w / 2
    target_center_y = roi_y + roi_h / 2

    # 2. Обчислити зміщення від центру екрана (прицілу) до центру ROI
    delta_x = target_center_x - screen_cx
    delta_y = target_center_y - screen_cy

    # 3. Застосувати "мертву зону"
    # Якщо відстань до цілі менша за поріг dead_zone, не рухати мишу
    distance = math.sqrt(delta_x ** 2 + delta_y ** 2)
    if distance < dead_zone:
        return

    # 4. Обчислити крок руху
    # Рух пропорційний відстані до цілі, що забезпечує плавність
    # та зменшення кроку при наближенні до цілі.
    # Використовуємо round() для отримання цілих значень пікселів для pydirectinput.
    move_x = int(round(delta_x * move_speed))
    move_y = int(round(delta_y * move_speed))

    # 5. Перемістити мишу відносно її поточної позиції
    # pydirectinput.moveRel() переміщує мишу відносно її поточного положення.
    # Оскільки ми розглядаємо screen_center як фіксований приціл,
    # відносний рух миші змінить "погляд" камери в грі так,
    # щоб ціль наблизилася до цього прицілу.
    if move_x != 0 or move_y != 0:
        pydirectinput.moveRel(move_x, move_y, relative=True)


# --- Приклад використання ---
if __name__ == '__main__':
    # Припустимо, розмір екрана 1920x1080
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080
    screen_center_coords = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    # Припустимо, виявлено ціль (наприклад, голову супротивника)
    # з координатами (x=1000, y=500) та розмірами 40x60 пікселів
    detected_target_roi = (1000, 500, 40, 60)  # (x, y, ширина, висота)

    print(f"Центр екрана (приціл): {screen_center_coords}")
    roi_x_center = detected_target_roi[0] + detected_target_roi[2] / 2
    roi_y_center = detected_target_roi[1] + detected_target_roi[3] / 2
    print(f"Центр цілі: ({roi_x_center}, {roi_y_center})")
    print("Імітація наведення миші (потрібно викликати цю функцію в циклі гри):")

    # Для демонстрації, ми можемо викликати функцію кілька разів,
    # щоб побачити, як вона намагається наблизити уявну мишу до цілі.
    # У реальній грі ця функція викликалася б на кожному кадрі або з певною частотою.

    # Важливо: pydirectinput фактично рухатиме вашою мишею!
    # Будьте обережні при тестуванні.
    # Щоб зупинити виконання, якщо щось піде не так, переключіться на інше вікно
    # або натисніть Ctrl+C в терміналі.

    # pydirectinput.PAUSE = 0.01 # Можна налаштувати затримку між діями pydirectinput
    # pydirectinput.FAILSAFE = True # Вмикає аварійну зупинку при переміщенні миші в кут екрана

    try:
        # Уявімо, що поточний центр прицілу збігається з центром екрана
        # і ми хочемо навестися на detected_target_roi.
        # У реальному циклі гри `screen_center_coords` завжди буде центром екрана,
        # а `target_mouse` буде коригувати "погляд" камери.

        # Імітуємо кілька кроків наведення:
        for i in range(20):  # Зробимо 20 кроків для демонстрації
            print(f"Крок {i + 1}: Наведення на ціль...")
            # У справжньому застосунку `screen_center_coords` залишатиметься сталим,
            # а сама гра реагуватиме на рухи миші.
            # Тут ми не оновлюємо `screen_center_coords` на основі руху миші,
            # бо функція розрахована на те, що `screen_center` - це фіксований приціл.
            target_mouse(detected_target_roi, screen_center_coords, dead_zone=5, move_speed=0.2)

            # Для симуляції того, що ціль стала ближче до центру після руху:
            # Це дуже груба симуляція, лише для ілюстрації.
            # У реальності, `detected_target_roi` буде оновлюватися детекцією об'єктів на екрані.
            # Або, якщо ми рухаємо "камеру", то сама ціль на екрані змінить свої координати.
            # Тут ми просто зменшуємо різницю для демонстрації збіжності.
            current_mouse_pos_estimate_x = screen_center_coords[0] + \
                                           (roi_x_center - screen_center_coords[0]) * (1 - 0.2) ** (i + 1)
            current_mouse_pos_estimate_y = screen_center_coords[1] + \
                                           (roi_y_center - screen_center_coords[1]) * (1 - 0.2) ** (i + 1)

            # Якщо ціль достатньо близько до центру, виходимо
            dist_x = roi_x_center - current_mouse_pos_estimate_x
            dist_y = roi_y_center - current_mouse_pos_estimate_y
            if math.sqrt(dist_x ** 2 + dist_y ** 2) < 5:  # 5 - це наша dead_zone
                print("Ціль досягнуто (в межах мертвої зони).")
                break

            # pydirectinput.sleep(0.05) # Невелика затримка між кроками для наочності

    except Exception as e:
        print(f"Сталася помилка: {e}")
    finally:
        print("Демонстрацію завершено.")