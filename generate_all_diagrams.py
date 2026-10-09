import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

os.makedirs("docs/assets", exist_ok=True)

# -------------------------------------------------------------
# DIAGRAM 2: ESQUEMA DE LIGAÇÃO (CIRCUITO COMPLETO DO PROJETO)
# -------------------------------------------------------------
def generate_circuit():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    ax.text(50, 96, "ESQUEMA ELÉTRICO DIDÁTICO DE CONEXÕES", fontsize=15, fontweight='bold', ha='center', color='#1b3a2b')
    ax.text(50, 92.5, "Como interligar o ESP32 aos componentes do sistema de irrigação", fontsize=9.5, ha='center', color='#4a5568')

    # Central Block: ESP32 DevKit
    esp_box = patches.FancyBboxPatch((38, 25), 24, 55, boxstyle="round,pad=1", facecolor="#1a202c", edgecolor="#4a5568", linewidth=2)
    ax.add_patch(esp_box)
    ax.text(50, 75, "ESP32 DevKit", fontsize=11, fontweight='bold', color="#ffffff", ha='center')
    ax.text(50, 71, "(Microcontrolador Central)", fontsize=8, color="#cbd5e0", ha='center')

    # ESP32 pin terminals (Left: 3V3, GND, VIN; Right: GPIO2, GPIO21, GPIO22, GPIO36)
    # Left terminals on ESP32
    term_vin = patches.Rectangle((37, 32), 2, 2.5, facecolor="#c53030")
    ax.add_patch(term_vin)
    ax.text(40, 33.25, "VIN (5V)", fontsize=7.5, color="#fc8181", va='center', fontweight='bold')

    term_gnd = patches.Rectangle((37, 38), 2, 2.5, facecolor="#2d3748")
    ax.add_patch(term_gnd)
    ax.text(40, 39.25, "GND (Terra)", fontsize=7.5, color="#e2e8f0", va='center', fontweight='bold')

    term_3v3 = patches.Rectangle((37, 44), 2, 2.5, facecolor="#dd6b20")
    ax.add_patch(term_3v3)
    ax.text(40, 45.25, "3V3 (3.3V)", fontsize=7.5, color="#fbd38d", va='center', fontweight='bold')

    # Right terminals on ESP32
    term_g2 = patches.Rectangle((61, 62), 2, 2.5, facecolor="#2b6cb0")
    ax.add_patch(term_g2)
    ax.text(60, 63.25, "GPIO 2", fontsize=7.5, color="#90cdf4", va='center', ha='right', fontweight='bold')

    term_g21 = patches.Rectangle((61, 52), 2, 2.5, facecolor="#805ad5")
    ax.add_patch(term_g21)
    ax.text(60, 53.25, "GPIO 21 (SDA)", fontsize=7.5, color="#d6bcfa", va='center', ha='right', fontweight='bold')

    term_g22 = patches.Rectangle((61, 46), 2, 2.5, facecolor="#805ad5")
    ax.add_patch(term_g22)
    ax.text(60, 47.25, "GPIO 22 (SCL)", fontsize=7.5, color="#d6bcfa", va='center', ha='right', fontweight='bold')

    term_g36 = patches.Rectangle((37, 56), 2, 2.5, facecolor="#319795")
    ax.add_patch(term_g36)
    ax.text(40, 57.25, "GPIO 36 / VP", fontsize=7.5, color="#81e6d9", va='center', fontweight='bold')

    # Component 1: Módulo Relé + Válvula (Right Top)
    rele_box = patches.FancyBboxPatch((74, 55), 23, 26, boxstyle="round,pad=0.8", facecolor="#2b6cb0", edgecolor="#2c5282", linewidth=1.5)
    ax.add_patch(rele_box)
    ax.text(85.5, 77, "MÓDULO RELÉ (5V)", fontsize=9.5, fontweight='bold', color="#ffffff", ha='center')
    ax.text(85.5, 73.5, "Aciona a Válvula Solenoide", fontsize=7.5, color="#bee3f8", ha='center')
    ax.text(76, 68, "• IN  <-- GPIO 2 (Sinal)", fontsize=7.5, color="#ffffff")
    ax.text(76, 64, "• VCC <-- VIN (5V)", fontsize=7.5, color="#ffffff")
    ax.text(76, 60, "• GND <-- GND (Terra)", fontsize=7.5, color="#ffffff")
    ax.text(85.5, 56.5, "[Contato Seco NA/COM] -> Válvula 12V", fontsize=7, color="#fed7d7", ha='center', style='italic')

    # Wire GPIO 2 to Relay IN
    ax.annotate("", xy=(74, 68), xytext=(63, 63.25),
                arrowprops=dict(arrowstyle="->", color="#2b6cb0", lw=2, shrinkA=0, shrinkB=0))

    # Component 2: RTC DS3231 (Right Bottom)
    rtc_box = patches.FancyBboxPatch((74, 18), 23, 30, boxstyle="round,pad=0.8", facecolor="#6b46c1", edgecolor="#553c9a", linewidth=1.5)
    ax.add_patch(rtc_box)
    ax.text(85.5, 44, "MÓDULO RTC DS3231", fontsize=9.5, fontweight='bold', color="#ffffff", ha='center')
    ax.text(85.5, 40.5, "Relógio em Tempo Real (Bateria)", fontsize=7.5, color="#e9d8fd", ha='center')
    ax.text(76, 35, "• VCC <-- 3V3 (3.3V)", fontsize=7.5, color="#ffffff")
    ax.text(76, 31, "• GND <-- GND (Terra)", fontsize=7.5, color="#ffffff")
    ax.text(76, 27, "• SDA <-- GPIO 21 (Dados I2C)", fontsize=7.5, color="#ffffff")
    ax.text(76, 23, "• SCL <-- GPIO 22 (Clock I2C)", fontsize=7.5, color="#ffffff")
    ax.text(85.5, 19.5, "Mantém a hora sem energia!", fontsize=7, color="#fefcbf", ha='center', style='italic')

    # Wires for RTC
    ax.annotate("", xy=(74, 27), xytext=(63, 53.25),
                arrowprops=dict(arrowstyle="->", color="#805ad5", lw=1.8, shrinkA=0, shrinkB=0))
    ax.annotate("", xy=(74, 23), xytext=(63, 47.25),
                arrowprops=dict(arrowstyle="->", color="#805ad5", lw=1.8, shrinkA=0, shrinkB=0))

    # Component 3: Sensor de Umidade Capacitivo (Left Top)
    sens_box = patches.FancyBboxPatch((3, 50), 25, 27, boxstyle="round,pad=0.8", facecolor="#234e52", edgecolor="#1d4044", linewidth=1.5)
    ax.add_patch(sens_box)
    ax.text(15.5, 73, "SENSOR DE UMIDADE", fontsize=9.5, fontweight='bold', color="#ffffff", ha='center')
    ax.text(15.5, 69.5, "Capacitivo V1.2 (Não oxida)", fontsize=7.5, color="#b2f5ea", ha='center')
    ax.text(5, 63.5, "• AOUT --> GPIO 36 / VP (Analógico)", fontsize=7.5, color="#ffffff")
    ax.text(5, 59.5, "• VCC  <-- 3V3 (Alimentação 3.3V)", fontsize=7.5, color="#ffffff")
    ax.text(5, 55.5, "• GND  <-- GND (Terra)", fontsize=7.5, color="#ffffff")
    ax.text(15.5, 52, "Mede a umidade da terra", fontsize=7, color="#e6fffa", ha='center', style='italic')

    # Wire Sensor AOUT to GPIO 36
    ax.annotate("", xy=(37, 57.25), xytext=(28, 63.5),
                arrowprops=dict(arrowstyle="->", color="#319795", lw=1.8, shrinkA=0, shrinkB=0))

    # Component 4: Barramento de Alimentação / Fonte (Left Bottom)
    pwr_box = patches.FancyBboxPatch((3, 14), 25, 28, boxstyle="round,pad=0.8", facecolor="#742a2a", edgecolor="#63171b", linewidth=1.5)
    ax.add_patch(pwr_box)
    ax.text(15.5, 38, "ALIMENTAÇÃO DO SISTEMA", fontsize=9.5, fontweight='bold', color="#ffffff", ha='center')
    ax.text(15.5, 34.5, "Fonte 5V USB / Externa", fontsize=7.5, color="#fed7d7", ha='center')
    ax.text(5, 29, "• 5V (+) -> Conectado ao VIN", fontsize=7.5, color="#ffffff")
    ax.text(5, 25, "• 0V (-) -> Conectado ao GND", fontsize=7.5, color="#ffffff")
    ax.text(5, 21, "• 3.3V   -> Gerado internamente", fontsize=7.5, color="#ffffff")
    ax.text(15.5, 16.5, "Alimenta todos os periféricos", fontsize=7, color="#fff5f5", ha='center', style='italic')

    # Power wires to ESP32
    ax.annotate("", xy=(37, 33.25), xytext=(28, 29),
                arrowprops=dict(arrowstyle="->", color="#e53e3e", lw=1.8, shrinkA=0, shrinkB=0))
    ax.annotate("", xy=(37, 39.25), xytext=(28, 25),
                arrowprops=dict(arrowstyle="->", color="#4a5568", lw=1.8, shrinkA=0, shrinkB=0))

    # Bottom notes
    note_box = patches.FancyBboxPatch((10, 1), 80, 8.5, boxstyle="round,pad=0.4", facecolor="#f7fafc", edgecolor="#cbd5e0")
    ax.add_patch(note_box)
    ax.text(12, 7, "★ SITUAÇÃO ATUAL DO CÓDIGO (FASE DE TESTES):", fontsize=8, fontweight='bold', color="#2b6cb0")
    ax.text(12, 4.5, "1. O pino GPIO 2 controla atualmente o LED azul onboard (simulação visual de abertura da válvula).", fontsize=7.5, color="#2d3748")
    ax.text(12, 2.3, "2. O relógio é ajustado pela página Web /admin. Na versão final, os pinos 21 e 22 lerão o RTC DS3231.", fontsize=7.5, color="#2d3748")

    plt.tight_layout()
    plt.savefig("docs/assets/circuit_diagram.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated: docs/assets/circuit_diagram.png")

# -------------------------------------------------------------
# DIAGRAM 3: FLUXO DE DECISÃO E ROTINAS DE SEGURANÇA
# -------------------------------------------------------------
def generate_flowchart():
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    ax.text(50, 96, "FLUXOGRAMA DE DECISÃO E SEGURANÇA", fontsize=15, fontweight='bold', ha='center', color='#1b3a2b')
    ax.text(50, 92.5, "Como o firmware decide se a água pode ou não ser liberada", fontsize=9.5, ha='center', color='#4a5568')

    # Step 1: Trigger Event
    s1 = patches.FancyBboxPatch((22, 80), 46, 8.5, boxstyle="round,pad=0.5", facecolor="#2f7d4f", edgecolor="#245f3d", linewidth=1.5)
    ax.add_patch(s1)
    ax.text(45, 84.2, "EVENTO DE DISPARO", fontsize=9, fontweight='bold', color="#ffffff", ha='center')
    ax.text(45, 81.5, "Horário Programado (RTC) OU Botão Manual (/admin/irrigate)", fontsize=7.5, color="#dcfce7", ha='center')

    # Arrow 1 down
    ax.annotate("", xy=(45, 73), xytext=(45, 80), arrowprops=dict(arrowstyle="->", color="#245f3d", lw=2))

    # Step 2: Cooldown Check
    s2 = patches.FancyBboxPatch((20, 61), 50, 11, boxstyle="round,pad=0.5", facecolor="#edf2f7", edgecolor="#cbd5e0", linewidth=1.5)
    ax.add_patch(s2)
    ax.text(45, 68, "TRAVA 1: Intervalo Mínimo (Cooldown)?", fontsize=9, fontweight='bold', color="#2d3748", ha='center')
    ax.text(45, 64, "Válvula aberta agora OU fechou há menos de 10s?", fontsize=7.8, color="#4a5568", ha='center')

    # Decision 1: SIM (Bloqueia) -> Right
    ax.annotate("", xy=(74, 66.5), xytext=(70, 66.5), arrowprops=dict(arrowstyle="->", color="#c53030", lw=2))
    ax.text(72, 68.5, "SIM", fontsize=7.5, fontweight='bold', color="#c53030", ha='center')
    b1 = patches.FancyBboxPatch((74, 62), 23, 9, boxstyle="round,pad=0.4", facecolor="#fed7d7", edgecolor="#feb2b2", linewidth=1.2)
    ax.add_patch(b1)
    ax.text(85.5, 67.5, "BLOCKED_COOLDOWN", fontsize=7.5, fontweight='bold', color="#9b2c2c", ha='center')
    ax.text(85.5, 64, "Bloqueia acionamento e\nregistra evento no histórico", fontsize=6.5, color="#742a2a", ha='center')

    # Decision 1: NÃO -> Down
    ax.annotate("", xy=(45, 54), xytext=(45, 61), arrowprops=dict(arrowstyle="->", color="#2f7d4f", lw=2))
    ax.text(47.5, 57.5, "NÃO", fontsize=7.5, fontweight='bold', color="#2f7d4f", ha='left')

    # Step 3: Daily Budget Check
    s3 = patches.FancyBboxPatch((20, 42), 50, 11, boxstyle="round,pad=0.5", facecolor="#edf2f7", edgecolor="#cbd5e0", linewidth=1.5)
    ax.add_patch(s3)
    ax.text(45, 49, "TRAVA 2: Orçamento Diário de Água?", fontsize=9, fontweight='bold', color="#2d3748", ha='center')
    ax.text(45, 45, "Tempo hoje + nova duração ultrapassa 900s (15 min)?", fontsize=7.8, color="#4a5568", ha='center')

    # Decision 2: SIM (Bloqueia) -> Right
    ax.annotate("", xy=(74, 47.5), xytext=(70, 47.5), arrowprops=dict(arrowstyle="->", color="#c53030", lw=2))
    ax.text(72, 49.5, "SIM", fontsize=7.5, fontweight='bold', color="#c53030", ha='center')
    b2 = patches.FancyBboxPatch((74, 43), 23, 9, boxstyle="round,pad=0.4", facecolor="#fed7d7", edgecolor="#feb2b2", linewidth=1.2)
    ax.add_patch(b2)
    ax.text(85.5, 48.5, "BLOCKED_DAILY_BUDGET", fontsize=7.5, fontweight='bold', color="#9b2c2c", ha='center')
    ax.text(85.5, 45, "Bloqueia acionamento e\nregistra evento no histórico", fontsize=6.5, color="#742a2a", ha='center')

    # Decision 2: NÃO -> Down
    ax.annotate("", xy=(45, 35), xytext=(45, 42), arrowprops=dict(arrowstyle="->", color="#2f7d4f", lw=2))
    ax.text(47.5, 38.5, "NÃO", fontsize=7.5, fontweight='bold', color="#2f7d4f", ha='left')

    # Step 4: Max Duration Clamp
    s4 = patches.FancyBboxPatch((20, 23), 50, 11, boxstyle="round,pad=0.5", facecolor="#edf2f7", edgecolor="#cbd5e0", linewidth=1.5)
    ax.add_patch(s4)
    ax.text(45, 30, "TRAVA 3: Teto Máximo de Duração", fontsize=9, fontweight='bold', color="#2d3748", ha='center')
    ax.text(45, 26, "Se duração > 300s (5 min), limita automaticamente a 300s", fontsize=7.8, color="#4a5568", ha='center')

    # Arrow down to Action
    ax.annotate("", xy=(45, 17), xytext=(45, 23), arrowprops=dict(arrowstyle="->", color="#2f7d4f", lw=2))

    # Step 5: Valve Activated
    s5 = patches.FancyBboxPatch((15, 4), 60, 12, boxstyle="round,pad=0.6", facecolor="#276749", edgecolor="#22543d", linewidth=2)
    ax.add_patch(s5)
    ax.text(45, 12.5, "★ VÁLVULA ABERTA COM SUCESSO!", fontsize=11, fontweight='bold', color="#ffffff", ha='center')
    ax.text(45, 8.5, "1. GPIO 2 aciona LED / Relé  |  2. Temporização precisa via millis()\n3. Registra no Histórico (SCHEDULE / MANUAL)  |  4. Desliga após N segundos", fontsize=7.2, color="#c6f6d5", ha='center')

    # Parada de emergência box on bottom right
    stop_box = patches.FancyBboxPatch((78, 4), 19, 12, boxstyle="round,pad=0.4", facecolor="#fff5f5", edgecolor="#e53e3e", linewidth=1.5)
    ax.add_patch(stop_box)
    ax.text(87.5, 12.5, "PARADA DE EMERGÊNCIA", fontsize=7.5, fontweight='bold', color="#c53030", ha='center')
    ax.text(87.5, 8, "Rota /admin/stop:\nFecha a válvula na hora e\ngrava EMERGENCY_STOP", fontsize=6.5, color="#742a2a", ha='center')

    plt.tight_layout()
    plt.savefig("docs/assets/safety_flowchart.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated: docs/assets/safety_flowchart.png")

# -------------------------------------------------------------
# DIAGRAM 4: ARQUITETURA GERAL DO SISTEMA
# -------------------------------------------------------------
def generate_architecture():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    ax.text(50, 96, "ARQUITETURA GERAL DO SISTEMA (OFFLINE)", fontsize=15, fontweight='bold', ha='center', color='#1b3a2b')
    ax.text(50, 92.5, "Visão sistêmica: do smartphone do usuário até a água na planta", fontsize=9.5, ha='center', color='#4a5568')

    # Layer 1: User / Smartphone
    u_box = patches.FancyBboxPatch((3, 44), 20, 38, boxstyle="round,pad=0.8", facecolor="#ebf8ff", edgecolor="#bee3f8", linewidth=1.5)
    ax.add_patch(u_box)
    ax.text(13, 76, "USUÁRIO", fontsize=10.5, fontweight='bold', color="#2b6cb0", ha='center')
    ax.text(13, 72, "(Hortelão / Aluno)", fontsize=7.5, color="#4a5568", ha='center')
    ax.text(13, 63, "Conecta ao Wi-Fi:\n'Irrigacao-Comunitaria'\n(senha: irrigacao)", fontsize=7.5, ha='center', color="#2d3748")
    ax.text(13, 52, "Abre no navegador:\nhttp://192.168.4.1", fontsize=7.8, fontweight='bold', ha='center', color="#2b6cb0")
    ax.text(13, 46, "100% Offline (Sem Internet)", fontsize=7, ha='center', color="#718096", style='italic')

    # Wi-Fi AP Arrow
    ax.annotate("", xy=(31, 63), xytext=(24, 63), arrowprops=dict(arrowstyle="<->", color="#3182ce", lw=2))
    ax.text(27.5, 68, "Wi-Fi Local\n(SoftAP)", fontsize=7.5, fontweight='bold', color="#2b6cb0", ha='center')
    ax.text(27.5, 57.5, "Sem roteador\nexterno", fontsize=6.8, color="#718096", ha='center')

    # Layer 2: ESP32 Firmware Core (Big Box)
    core_box = patches.FancyBboxPatch((32, 12), 40, 75, boxstyle="round,pad=1", facecolor="#f7fafc", edgecolor="#cbd5e0", linewidth=2)
    ax.add_patch(core_box)
    ax.text(52, 83.5, "ESP32 FIRMWARE (C++ / Arduino)", fontsize=11, fontweight='bold', color="#1a202c", ha='center')

    # Sub-block: Web Server
    ws_box = patches.FancyBboxPatch((34, 61), 36, 17, boxstyle="round,pad=0.5", facecolor="#e6fffa", edgecolor="#b2f5ea")
    ax.add_patch(ws_box)
    ax.text(52, 74, "Módulo Web Server (web_server.cpp)", fontsize=9, fontweight='bold', color="#234e52", ha='center')
    ax.text(52, 69, "• Página /status: Painel visual em tempo real\n• Página /admin: Ajuste de horários e testes\n• API /status.json e exportação CSV de histórico", fontsize=7, color="#285e61", ha='center')

    # Sub-block: Lógica e Segurança
    ls_box = patches.FancyBboxPatch((34, 38), 36, 19, boxstyle="round,pad=0.5", facecolor="#feebc8", edgecolor="#fbd38d")
    ax.add_patch(ls_box)
    ax.text(52, 53, "Lógica & Segurança (main.cpp + logic)", fontsize=9, fontweight='bold', color="#744210", ha='center')
    ax.text(52, 47, "• decideIrrigation(): Compara RTC com agendamentos\n• Travas: Cooldown (10s), Orçamento (15m), Teto (5m)\n• Botão de Parada de Emergência (/admin/stop)", fontsize=7, color="#744210", ha='center')

    # Sub-block: Armazenamento SPIFFS
    st_box = patches.FancyBboxPatch((34, 15), 36, 19, boxstyle="round,pad=0.5", facecolor="#fed7e2", edgecolor="#fbb6ce")
    ax.add_patch(st_box)
    ax.text(52, 30, "Memória Flash SPIFFS (storage.cpp)", fontsize=9, fontweight='bold', color="#702459", ha='center')
    ax.text(52, 24, "• /config.bin: Horários e duração da rega salvos\n• /history.bin: Log permanente de todos os eventos\n(Dados não se perdem ao desligar da tomada)", fontsize=7, color="#702459", ha='center')

    # Internal arrows in ESP32
    ax.annotate("", xy=(52, 58), xytext=(52, 61), arrowprops=dict(arrowstyle="<->", color="#718096", lw=1.5))
    ax.annotate("", xy=(52, 35), xytext=(52, 38), arrowprops=dict(arrowstyle="<->", color="#718096", lw=1.5))

    # Layer 3: Physical Actuators & Sensors (Right)
    act_box = patches.FancyBboxPatch((76, 51), 21, 31, boxstyle="round,pad=0.8", facecolor="#f0fff4", edgecolor="#9ae6b4", linewidth=1.5)
    ax.add_patch(act_box)
    ax.text(86.5, 77.5, "ATUADORES", fontsize=10, fontweight='bold', color="#22543d", ha='center')
    ax.text(86.5, 71, "GPIO 2\nLED Onboard\n(Fase de Mock/Testes)", fontsize=7.5, ha='center', color="#276749")
    ax.text(86.5, 59, "↓ No Hardware Real ↓\nMódulo Relé 5V\nVálvula Solenoide 12V", fontsize=7.5, fontweight='bold', ha='center', color="#22543d")

    sens_right = patches.FancyBboxPatch((76, 15), 21, 32, boxstyle="round,pad=0.8", facecolor="#faf5ff", edgecolor="#d6bcfa", linewidth=1.5)
    ax.add_patch(sens_right)
    ax.text(86.5, 42.5, "SENSORES (FUTURO)", fontsize=9.5, fontweight='bold', color="#553c9a", ha='center')
    ax.text(86.5, 34, "RTC DS3231\n(I2C: GPIO 21 e 22)\nHorário exato permanente", fontsize=7.2, ha='center', color="#6b46c1")
    ax.text(86.5, 22.5, "Sensor Umidade\n(ADC: GPIO 36)\nLeitura capacitiva do solo", fontsize=7.2, ha='center', color="#553c9a")

    # Connect ESP32 to Hardware
    ax.annotate("", xy=(75, 68), xytext=(71, 53),
                arrowprops=dict(arrowstyle="->", color="#276749", lw=2))
    ax.annotate("", xy=(71, 44), xytext=(75, 30),
                arrowprops=dict(arrowstyle="<-", color="#6b46c1", lw=1.8))

    plt.tight_layout()
    plt.savefig("docs/assets/system_architecture.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated: docs/assets/system_architecture.png")

generate_circuit()
generate_flowchart()
generate_architecture()
