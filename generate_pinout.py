import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import os

# Create docs/assets directory if not exists
os.makedirs("docs/assets", exist_ok=True)

# -------------------------------------------------------------
# DIAGRAM 1: ESP32 PINOUT (DEVKIT V1 - 30 PINS)
# -------------------------------------------------------------
def generate_pinout():
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Background
    fig.patch.set_facecolor('#ffffff')

    # Title
    ax.text(50, 96, "DIAGRAMA DE PINAGEM - ESP32 DEVKIT V1", fontsize=16, fontweight='bold', ha='center', color='#1b3a2b')
    ax.text(50, 93, "Identificação dos Pinos e Funções no Projeto de Irrigação", fontsize=10, ha='center', color='#4a5568')

    # Draw ESP32 Board
    # Main PCB board
    pcb = patches.FancyBboxPatch((35, 12), 30, 76, boxstyle="round,pad=1.2,rounding_size=2",
                                 facecolor="#1a202c", edgecolor="#4a5568", linewidth=2.5)
    ax.add_patch(pcb)

    # Antenna (metal shield / trace at top)
    ant = patches.Rectangle((41, 79), 18, 9, facecolor="#b7791f", edgecolor="#d69e2e", linewidth=1.5)
    ax.add_patch(ant)
    ax.text(50, 83.5, "ANTENA WI-FI", fontsize=7.5, color='#ffffff', fontweight='bold', ha='center')

    # ESP-WROOM-32 Shield
    shield = patches.Rectangle((39, 44), 22, 32, facecolor="#718096", edgecolor="#cbd5e0", linewidth=1.5)
    ax.add_patch(shield)
    ax.text(50, 62, "ESP-WROOM-32", fontsize=9, color='#ffffff', fontweight='bold', ha='center')
    ax.text(50, 58, "Dual-Core 240MHz\nWi-Fi & BLE", fontsize=7, color='#e2e8f0', ha='center')

    # USB Port at bottom
    usb = patches.Rectangle((44, 8), 12, 6, facecolor="#cbd5e0", edgecolor="#4a5568", linewidth=1.5)
    ax.add_patch(usb)
    ax.text(50, 11, "MICRO-USB", fontsize=6.5, color='#2d3748', fontweight='bold', ha='center')

    # Onboard LED (GPIO 2)
    led_box = patches.Circle((43, 38), 1.8, facecolor="#3182ce", edgecolor="#bee3f8", linewidth=1.5)
    ax.add_patch(led_box)
    ax.text(43, 33.5, "LED AZUL\n(GPIO 2)", fontsize=6.5, color='#63b3ed', fontweight='bold', ha='center')

    # Power LED
    pwr_led = patches.Circle((57, 38), 1.8, facecolor="#e53e3e", edgecolor="#fed7d7", linewidth=1.5)
    ax.add_patch(pwr_led)
    ax.text(57, 33.5, "LED PWR\n(Vermelho)", fontsize=6.5, color='#fc8181', ha='center')

    # Reset & Boot Buttons
    btn_en = patches.FancyBboxPatch((37, 20), 6, 6, boxstyle="round,pad=0.3", facecolor="#2d3748", edgecolor="#718096", linewidth=1)
    ax.add_patch(btn_en)
    ax.text(40, 23, "EN\nRST", fontsize=5.5, color="#ffffff", ha='center', va='center', fontweight='bold', linespacing=0.9)

    btn_boot = patches.FancyBboxPatch((57, 20), 6, 6, boxstyle="round,pad=0.3", facecolor="#2d3748", edgecolor="#718096", linewidth=1)
    ax.add_patch(btn_boot)
    ax.text(60, 23, "IO0\nBOOT", fontsize=5.5, color="#ffffff", ha='center', va='center', fontweight='bold', linespacing=0.9)

    # Left & Right Pin Lists (30-pin board)
    left_pins = [
        ("EN", "Enable / Reset", "#718096"),
        ("VP (GPIO36)", "Sensor Umidade (ADC futuro)", "#319795"),
        ("VN (GPIO39)", "ADC / Entrada Analógica", "#718096"),
        ("D34 (GPIO34)", "ADC / Entrada Analógica", "#718096"),
        ("D35 (GPIO35)", "ADC / Entrada Analógica", "#718096"),
        ("D32 (GPIO32)", "GPIO / Touch / ADC", "#718096"),
        ("D33 (GPIO33)", "GPIO / Touch / ADC", "#718096"),
        ("D25 (GPIO25)", "GPIO / DAC1", "#718096"),
        ("D26 (GPIO26)", "GPIO / DAC2", "#718096"),
        ("D27 (GPIO27)", "GPIO / Touch", "#718096"),
        ("D14 (GPIO14)", "GPIO / PWM", "#718096"),
        ("D12 (GPIO12)", "GPIO / PWM", "#718096"),
        ("D13 (GPIO13)", "GPIO / PWM", "#718096"),
        ("GND", "Terra / Negativo Comum", "#2d3748"),
        ("VIN (5V)", "Entrada 5V Fonte/USB", "#c53030"),
    ]

    right_pins = [
        ("D23 (GPIO23)", "GPIO / SPI MOSI", "#718096"),
        ("D22 (GPIO22)", "I2C SCL (RTC DS3231 futuro)", "#805ad5"),
        ("TX0 (GPIO1)", "Serial TX", "#718096"),
        ("RX0 (GPIO3)", "Serial RX", "#718096"),
        ("D21 (GPIO21)", "I2C SDA (RTC DS3231 futuro)", "#805ad5"),
        ("D19 (GPIO19)", "GPIO / SPI MISO", "#718096"),
        ("D18 (GPIO18)", "GPIO / SPI SCK", "#718096"),
        ("D5 (GPIO5)", "GPIO / Saída", "#718096"),
        ("TX2 (GPIO17)", "GPIO / Serial 2", "#718096"),
        ("RX2 (GPIO16)", "GPIO / Serial 2", "#718096"),
        ("D4 (GPIO4)", "GPIO / Uso Geral", "#718096"),
        ("D2 (GPIO2)", "★ VÁLVULA / LED ONBOARD", "#2b6cb0"),
        ("D15 (GPIO15)", "GPIO / PWM", "#718096"),
        ("GND", "Terra / Negativo Comum", "#2d3748"),
        ("3V3 (3.3V)", "Alimentação 3.3V Sensores", "#dd6b20"),
    ]

    y_start = 74
    y_step = 4.1

    # Draw Left Pins
    for i, (pname, pdesc, color) in enumerate(left_pins):
        y = y_start - i * y_step
        # Pin metal connector
        pin_metal = patches.Rectangle((33, y - 0.7), 2.5, 1.4, facecolor="#e2e8f0", edgecolor="#4a5568")
        ax.add_patch(pin_metal)

        # Pin label inside board
        ax.text(37, y, pname.split()[0], fontsize=7, color="#cbd5e0", va='center', ha='left', fontweight='bold')

        # External tag box
        is_highlight = color != "#718096"
        tag_bg = color if is_highlight else "#edf2f7"
        tag_fg = "#ffffff" if is_highlight else "#4a5568"
        border_col = color if is_highlight else "#cbd5e0"

        tag = patches.FancyBboxPatch((2, y - 1.4), 28, 2.8, boxstyle="round,pad=0.2",
                                     facecolor=tag_bg, edgecolor=border_col, linewidth=1.2)
        ax.add_patch(tag)
        ax.text(3, y, pname, fontsize=7.5, fontweight='bold', color=tag_fg, va='center')
        ax.text(29, y, pdesc, fontsize=6.5, color=tag_fg, va='center', ha='right', style='italic' if not is_highlight else 'normal')

        # Line connecting tag to pin
        ax.plot([30, 33], [y, y], color=border_col, linewidth=1, linestyle=":")

    # Draw Right Pins
    for i, (pname, pdesc, color) in enumerate(right_pins):
        y = y_start - i * y_step
        # Pin metal connector
        pin_metal = patches.Rectangle((64.5, y - 0.7), 2.5, 1.4, facecolor="#e2e8f0", edgecolor="#4a5568")
        ax.add_patch(pin_metal)

        # Pin label inside board
        ax.text(63, y, pname.split()[0], fontsize=7, color="#cbd5e0", va='center', ha='right', fontweight='bold')

        # External tag box
        is_highlight = color != "#718096"
        tag_bg = color if is_highlight else "#edf2f7"
        tag_fg = "#ffffff" if is_highlight else "#4a5568"
        border_col = color if is_highlight else "#cbd5e0"

        tag = patches.FancyBboxPatch((70, y - 1.4), 28, 2.8, boxstyle="round,pad=0.2",
                                     facecolor=tag_bg, edgecolor=border_col, linewidth=1.2)
        ax.add_patch(tag)
        ax.text(71, y, pname, fontsize=7.5, fontweight='bold', color=tag_fg, va='center')
        ax.text(97, y, pdesc, fontsize=6.5, color=tag_fg, va='center', ha='right', style='italic' if not is_highlight else 'normal')

        # Line connecting tag to pin
        ax.plot([67, 70], [y, y], color=border_col, linewidth=1, linestyle=":")

    # Legend at bottom
    leg_box = patches.FancyBboxPatch((10, 1), 80, 5.5, boxstyle="round,pad=0.4",
                                     facecolor="#f7fafc", edgecolor="#cbd5e0", linewidth=1)
    ax.add_patch(leg_box)
    ax.text(12, 4.3, "LEGENDA DE CORES:", fontsize=7.5, fontweight='bold', color="#2d3748")

    legends = [
        ("Azul: Válvula / LED (GPIO 2 - Ativo)", "#2b6cb0"),
        ("Roxo: I2C p/ RTC DS3231 (GPIO 21/22)", "#805ad5"),
        ("Verde Petróleo: Sensor Umidade (GPIO 36)", "#319795"),
        ("Vermelho/Laranja: Alimentação 5V / 3.3V", "#c53030"),
        ("Preto: GND (Negativo)", "#2d3748"),
    ]
    for idx, (ltxt, lcol) in enumerate(legends):
        lx = 12 + (idx % 3) * 26
        ly = 2.4 if idx < 3 else 1.2
        lsq = patches.Rectangle((lx, ly - 0.2), 2, 0.9, facecolor=lcol, edgecolor="#ffffff")
        ax.add_patch(lsq)
        ax.text(lx + 2.6, ly + 0.2, ltxt, fontsize=6.2, color="#2d3748", va='center')

    plt.tight_layout()
    plt.savefig("docs/assets/esp32_pinout.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated: docs/assets/esp32_pinout.png")

generate_pinout()
