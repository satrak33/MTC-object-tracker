import pydirectinput
import math

# Рекомендація: pydirectinput може вимагати прав адміністратора.
# Встановлення: pip install pydirectinput

def target_mouse(target_roi: tuple[int, int, int, int],
                 screen_center: tuple[int, int],
                 dead_zone: int = 5,
                 move_speed: float = 0.2) -> None: # Зверніть увагу на рекомендоване значення move_speed
    """
    Плавно переміщує курсор миші до центру вказаного регіону (ROI).

    Працює подібно до прицілювання в FPS, де 'screen_center' є поточною позицією прицілу.
    Ключ до стабільності - правильний підбір `move_speed`.

    Args:
        target_roi (tuple[int, int, int, int]): Координати цільової області
                                                  у форматі (x, y, ширина, висота).
        screen_center (tuple[int, int]): Координати центру екрана (поточного прицілу)
                                           у форматі (cx, cy).
        dead_zone (int, optional): Мінімальна відстань до цілі (в пікселях) для активації руху.
                                   Запобігає тремтінню при малих відхиленнях. Defaults to 5.
        move_speed (float, optional): Коефіцієнт швидкості руху (від 0.0 до 1.0).
                                     ВАЖЛИВО: Почніть з ДУЖЕ НИЗЬКОГО значення (наприклад, 0.05 - 0.1).
                                     Занадто високе значення призведе до нестабільності,
                                     перельотів та коливань ("зриву" руху).
                                     Поступово збільшуйте для досягнення балансу
                                     швидкості та плавності. Defaults to 0.1.
    """
    roi_x, roi_y, roi_w, roi_h = target_roi
    screen_cx, screen_cy = screen_center

    target_center_x = roi_x + roi_w / 2
    target_center_y = roi_y + roi_h / 2

    delta_x = target_center_x - screen_cx
    delta_y = target_center_y - screen_cy

    distance = math.sqrt(delta_x**2 + delta_y**2)
    if distance < dead_zone:
        # print(f"Ціль в мертвій зоні. Відстань: {distance:.2f}") # Для дебагу
        return

    # Розрахунок кроку руху. `move_speed` визначає агресивність.
    move_x = int(round(delta_x * move_speed))
    move_y = int(round(delta_y * move_speed))

    # Для дебагу: виведення розрахункових значень
    # print(f"ROI: {target_roi}, Target Center: ({target_center_x:.2f}, {target_center_y:.2f})")
    # print(f"Screen Center: {screen_center}")
    # print(f"Delta: ({delta_x:.2f}, {delta_y:.2f}), Distance: {distance:.2f}")
    # print(f"Calculated Move: ({move_x}, {move_y}) with move_speed: {move_speed}")

    if move_x != 0 or move_y != 0:
        pydirectinput.moveRel(move_x, move_y, relative=True)
        # print(f"Мишу переміщено на: ({move_x}, {move_y})") # Для дебагу
    # else:
        # print("Розрахунковий рух нульовий (після округлення), але поза мертвою зоною.") # Для дебагу

# --- Концептуальний приклад використання в ігровому циклі ---
# Цей код НЕ є самостійною робочою програмою, а показує логіку інтеграції.
