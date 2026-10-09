import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

os.makedirs("docs/assets", exist_ok=True)

# -------------------------------------------------------------
# DIAGRAM 5: DEFESA EM PROFUNDIDADE (CAMADAS DE SEGURANÇA)
# -------------------------------------------------------------
def generate_defense_in_depth():
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    ax.text(50, 95, "ARQUITETURA DE SEGURANÇA: DEFESA EM PROFUNDIDADE", fontsize=15, fontweight='bold', ha='center', color='#1b4332')
    ax.text(50, 91.5, "Quatro barreiras defensivas em cascata protegem a horta contra falhas e erros humanos", fontsize=9.5, ha='center', color='#4a5568')

    # Layer 1: Input & Timing Gate
    c1 = patches.FancyBboxPatch((5, 68), 90, 18, boxstyle="round,pad=0.8", facecolor="#eff6ff", edgecolor="#93c5fd", linewidth=1.5)
    ax.add_patch(c1)
    ax.text(8, 81, "CAMADA 1: FILTRAGEM DE ENTRADA & DEDUPLICAÇÃO", fontsize=10, fontweight='bold', color="#1e40af")
    ax.text(8, 76, "• Deduplicação de Minuto (currentMinuteKey): Impede 60 disparos repetidos no mesmo minuto de agendamento.", fontsize=7.8, color="#1e3a8a")
    ax.text(8, 71.5, "• Validação de Calendário (isValidCalendarDateTime): Checa dias de 1 a 31 e anos bissextos antes de aceitar /admin/time.", fontsize=7.8, color="#1e3a8a")

    # Arrow down
    ax.annotate("", xy=(50, 64), xytext=(50, 68), arrowprops=dict(arrowstyle="->", color="#2563eb", lw=2))

    # Layer 2: Cooldown Gate
    c2 = patches.FancyBboxPatch((5, 46), 90, 18, boxstyle="round,pad=0.8", facecolor="#fef3c7", edgecolor="#fcd34d", linewidth=1.5)
    ax.add_patch(c2)
    ax.text(8, 59, "CAMADA 2: CONTROLE DE ESTADO & COOLDOWN (10s)", fontsize=10, fontweight='bold', color="#92400e")
    ax.text(8, 54, "• Bloqueio se valveOpen == true: Impede reabertura enquanto a válvula ainda está em funcionamento.", fontsize=7.8, color="#78350f")
    ax.text(8, 49.5, "• Cooldown pós-fechamento (IRRIGATION_COOLDOWN_SEC): Intervalo de 10s contra choques hidráulicos (golpe de aríete).", fontsize=7.8, color="#78350f")

    # Arrow down
    ax.annotate("", xy=(50, 42), xytext=(50, 46), arrowprops=dict(arrowstyle="->", color="#d97706", lw=2))

    # Layer 3: Daily Budget Gate
    c3 = patches.FancyBboxPatch((5, 24), 90, 18, boxstyle="round,pad=0.8", facecolor="#fed7aa", edgecolor="#fb923c", linewidth=1.5)
    ax.add_patch(c3)
    ax.text(8, 37, "CAMADA 3: ORÇAMENTO DIÁRIO DE ÁGUA (DAILY WATER BUDGET - 900s / 15 MIN)", fontsize=10, fontweight='bold', color="#9a3412")
    ax.text(8, 32, "• Teto de Consumo Acumulado: Soma o tempo total aberto no dia. Bloqueia regas se consumo + nova duração > 900s.", fontsize=7.8, color="#7c2d12")
    ax.text(8, 27.5, "• Reinício Automático por Epoch (resetDailyBudgetIfNewDay): Zera a cota automaticamente a cada virada de dia solar.", fontsize=7.8, color="#7c2d12")

    # Arrow down
    ax.annotate("", xy=(50, 20), xytext=(50, 24), arrowprops=dict(arrowstyle="->", color="#ea580c", lw=2))

    # Layer 4: Execution & Kill Switch
    c4 = patches.FancyBboxPatch((5, 2), 90, 18, boxstyle="round,pad=0.8", facecolor="#dcfce7", edgecolor="#86efac", linewidth=2)
    ax.add_patch(c4)
    ax.text(8, 15, "CAMADA 4: TETO FÍSICO POR ACIONAMENTO (300s) & PARADA DE EMERGÊNCIA", fontsize=10, fontweight='bold', color="#166534")
    ax.text(8, 10, "• Teto Absoluto Unitário (MAX_IRRIGATION_DURATION_SEC): Poda sumária para 300s (5 min), mesmo se digitado valor absurdo.", fontsize=7.8, color="#14532d")
    ax.text(8, 5.5, "• Botão de Emergência (/admin/stop): Desliga o pino GPIO 2 instantaneamente e audita com EMERGENCY_STOP.", fontsize=7.8, color="#14532d")

    plt.tight_layout()
    plt.savefig("docs/assets/defense_in_depth.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated: docs/assets/defense_in_depth.png")

# -------------------------------------------------------------
# DIAGRAM 6: TIMELINE VISUAL DO ORÇAMENTO DIÁRIO
# -------------------------------------------------------------
def generate_budget_timeline():
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    ax.text(50, 95, "SIMULAÇÃO DO ORÇAMENTO DIÁRIO DE ÁGUA (900s / 15 MIN)", fontsize=15, fontweight='bold', ha='center', color='#1b4332')
    ax.text(50, 91.5, "Como o sistema rastreia e protege o consumo ao longo de 24 horas", fontsize=9.5, ha='center', color='#4a5568')

    # Main timeline bar
    tl_bg = patches.Rectangle((8, 62), 84, 8, facecolor="#e2e8f0", edgecolor="#cbd5e1", linewidth=1.5)
    ax.add_patch(tl_bg)

    # Segments on timeline
    # 06:30 -> 300s (green)
    s1 = patches.Rectangle((8, 62), 28, 8, facecolor="#22c55e", edgecolor="#16a34a", linewidth=1)
    ax.add_patch(s1)
    ax.text(22, 66, "Rega 1 (06:30): 300s", fontsize=7.5, color="#ffffff", ha='center', va='center', fontweight='bold')

    # 12:00 -> 300s (green)
    s2 = patches.Rectangle((36, 62), 28, 8, facecolor="#22c55e", edgecolor="#16a34a", linewidth=1)
    ax.add_patch(s2)
    ax.text(50, 66, "Rega 2 (12:00): 300s", fontsize=7.5, color="#ffffff", ha='center', va='center', fontweight='bold')

    # 17:30 -> 300s (green) - Reaches 900s!
    s3 = patches.Rectangle((64, 62), 28, 8, facecolor="#22c55e", edgecolor="#16a34a", linewidth=1)
    ax.add_patch(s3)
    ax.text(78, 66, "Rega 3 (17:30): 300s", fontsize=7.5, color="#ffffff", ha='center', va='center', fontweight='bold')

    # Labels below timeline
    ax.text(8, 57, "00:00 (Reset: 0s)", fontsize=7.5, color="#4a5568", ha='center')
    ax.text(36, 57, "Acumulado: 300s", fontsize=7.5, color="#4a5568", ha='center')
    ax.text(64, 57, "Acumulado: 600s", fontsize=7.5, color="#4a5568", ha='center')
    ax.text(92, 57, "TETO ATINGIDO (900s)", fontsize=7.5, fontweight='bold', color="#b91c1c", ha='center')

    # Event: 4th attempt at 19:00 -> BLOCKED!
    box_blocked = patches.FancyBboxPatch((15, 20), 70, 28, boxstyle="round,pad=0.8", facecolor="#fef2f2", edgecolor="#f87171", linewidth=1.5)
    ax.add_patch(box_blocked)
    ax.text(50, 42, "CENÁRIO CRÍTICO: 4ª TENTATIVA DE REGAS ÀS 19:00 (MANUAL OU AGENDADA)", fontsize=9.5, fontweight='bold', color="#991b1b", ha='center')
    ax.text(50, 36.5, "• Pedido de rega solicitado: 120 segundos.", fontsize=8, color="#7f1d1d", ha='center')
    ax.text(50, 31.5, "• Verificação do Firmware: 900s (já gastos) + 120s = 1020s > 900s (DAILY_WATER_BUDGET_SEC).", fontsize=8, color="#7f1d1d", ha='center')
    ax.text(50, 26.5, "• AÇÃO DO SISTEMA: Válvula NÃO abre! Requisição rejeitada instantaneamente.", fontsize=8.5, fontweight='bold', color="#b91c1c", ha='center')
    ax.text(50, 22, "• REGISTRO NO HISTÓRICO: Gravado como BLOCKED_DAILY_BUDGET com data e hora exatas.", fontsize=7.8, color="#7f1d1d", ha='center')

    # Arrow from timeline end to blocked box
    ax.annotate("", xy=(85, 48), xytext=(92, 60), arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=2, connectionstyle="arc3,rad=0.2"))

    # Bottom reset note
    ax.text(50, 8, "★ Às 00:00 do dia seguinte (novo dayIndex), o contador reinicia para 0s automaticamente.", fontsize=8, fontweight='bold', color="#1b4332", ha='center')

    plt.tight_layout()
    plt.savefig("docs/assets/budget_timeline.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated: docs/assets/budget_timeline.png")

generate_defense_in_depth()
generate_budget_timeline()
