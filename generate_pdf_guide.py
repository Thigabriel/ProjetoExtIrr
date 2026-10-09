"""
Script gerador do Guia Didático e Completo do Projeto de Irrigação com ESP32.
Gera um PDF profissional, ricamente formatado, com imagens, diagramas e linguagem acessível.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# Dimensões da folha A4 em pontos (595.27 x 841.89)
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 40
PRINTABLE_WIDTH = PAGE_WIDTH - 2 * MARGIN

# Cores da Identidade Visual do Projeto
PRIMARY_DARK = colors.HexColor("#1b4332")      # Verde Floresta Escuro (Capa / H1)
PRIMARY = colors.HexColor("#2d6a4f")           # Verde Médio
ACCENT = colors.HexColor("#52b788")            # Verde Menta
BG_LIGHT = colors.HexColor("#f8fafc")          # Cinza clarinho de fundo
TEXT_DARK = colors.HexColor("#1e293b")         # Cinza Quase Preto (legibilidade alta)
MUTED = colors.HexColor("#64748b")             # Cinza Médio para notas
BORDER_COLOR = colors.HexColor("#e2e8f0")      # Borda sutil
ALERT_RED = colors.HexColor("#b91c1c")         # Vermelho Alerta
ALERT_BG = colors.HexColor("#fef2f2")          # Fundo Vermelho
NOTE_BLUE = colors.HexColor("#1d4ed8")         # Azul Dica
NOTE_BG = colors.HexColor("#eff6ff")           # Fundo Azul
AMBER_TIP = colors.HexColor("#b45309")         # Âmbar Analogia
AMBER_BG = colors.HexColor("#fffbeb")          # Fundo Âmbar


class NumberedCanvas(canvas.Canvas):
    """
    Canvas de duas passagens: calcula o total de páginas dinamicamente
    e desenha cabeçalhos e rodapés com numeração 'Página X de Y'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, total_pages):
        # Na capa (página 1), não desenha cabeçalho nem rodapé
        if self._pageNumber == 1:
            return

        self.saveState()

        # Cabeçalho Superior
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(PRIMARY)
        self.drawString(MARGIN, 812, "PROJETO DE EXTENSÃO UNIVERSITÁRIA • IRRIGAÇÃO AUTOMATIZADA ESP32")
        self.setFont("Helvetica", 8)
        self.setFillColor(MUTED)
        self.drawRightString(PAGE_WIDTH - MARGIN, 812, "GUIA DIDÁTICO DO FIRMWARE")

        # Linha divisória do cabeçalho
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.6)
        self.line(MARGIN, 806, PAGE_WIDTH - MARGIN, 806)

        # Linha divisória do rodapé
        self.line(MARGIN, 44, PAGE_WIDTH - MARGIN, 44)

        # Rodapé Inferior
        self.drawString(MARGIN, 32, "Documentação Técnica & Educacional • Sistema de Irrigação Offline")
        page_str = f"Página {self._pageNumber} de {total_pages}"
        self.drawRightString(PAGE_WIDTH - MARGIN, 32, page_str)

        self.restoreState()


def get_styles():
    """Gera a folha de estilos tipográficos para o documento."""
    base = getSampleStyleSheet()

    styles = {
        'CoverBadge': ParagraphStyle(
            'CoverBadge',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=13,
            textColor=PRIMARY,
            alignment=1,
            spaceAfter=14
        ),
        'CoverTitle': ParagraphStyle(
            'CoverTitle',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=26,
            leading=32,
            textColor=PRIMARY_DARK,
            alignment=1,
            spaceAfter=12
        ),
        'CoverSubtitle': ParagraphStyle(
            'CoverSubtitle',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=13,
            leading=18,
            textColor=TEXT_DARK,
            alignment=1,
            spaceAfter=20
        ),
        'CoverDesc': ParagraphStyle(
            'CoverDesc',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=MUTED,
            alignment=1
        ),
        'H1': ParagraphStyle(
            'Heading1_Custom',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=PRIMARY_DARK,
            spaceBefore=8,
            spaceAfter=8,
            keepWithNext=True
        ),
        'H2': ParagraphStyle(
            'Heading2_Custom',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=PRIMARY,
            spaceBefore=10,
            spaceAfter=5,
            keepWithNext=True
        ),
        'H3': ParagraphStyle(
            'Heading3_Custom',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            textColor=TEXT_DARK,
            spaceBefore=8,
            spaceAfter=3,
            keepWithNext=True
        ),
        'Body': ParagraphStyle(
            'Body_Custom',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13.5,
            textColor=TEXT_DARK,
            spaceAfter=6
        ),
        'BodyBold': ParagraphStyle(
            'BodyBold_Custom',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=13.5,
            textColor=TEXT_DARK,
            spaceAfter=6
        ),
        'CodeSnippet': ParagraphStyle(
            'CodeSnippet',
            parent=base['Normal'],
            fontName='Courier',
            fontSize=7.5,
            leading=10.5,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=2,
            spaceAfter=2
        ),
        'Caption': ParagraphStyle(
            'Caption',
            parent=base['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=MUTED,
            alignment=1,
            spaceAfter=8
        ),
        'CalloutTitle': ParagraphStyle(
            'CalloutTitle',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            spaceAfter=2
        ),
        'CalloutText': ParagraphStyle(
            'CalloutText',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=TEXT_DARK
        ),
        'TableHeader': ParagraphStyle(
            'TableHeader',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.white,
            alignment=1
        ),
        'TableCell': ParagraphStyle(
            'TableCell',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=TEXT_DARK
        ),
        'TableCellBold': ParagraphStyle(
            'TableCellBold',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            textColor=PRIMARY_DARK
        ),
    }
    return styles


def callout_box(title, text, box_type="tip", styles=None):
    """Cria uma caixa destacada estilizada (Dica, Analogia ou Atenção)."""
    if box_type == "tip":
        border_col = NOTE_BLUE
        bg_col = NOTE_BG
        title_col = NOTE_BLUE
        icon = "💡 DICA TÉCNICA:"
    elif box_type == "analogy":
        border_col = AMBER_TIP
        bg_col = AMBER_BG
        title_col = AMBER_TIP
        icon = "🌱 ANALOGIA DO COTIDIANO:"
    elif box_type == "alert":
        border_col = ALERT_RED
        bg_col = ALERT_BG
        title_col = ALERT_RED
        icon = "⚠️ ATENÇÃO / SEGURANÇA:"
    else:
        border_col = PRIMARY
        bg_col = BG_LIGHT
        title_col = PRIMARY_DARK
        icon = "📌 NOTA DIDÁTICA:"

    t_style = ParagraphStyle('CBTitle', parent=styles['CalloutTitle'], textColor=title_col)
    content = [
        Paragraph(f"<b>{icon} {title}</b>", t_style),
        Spacer(1, 2),
        Paragraph(text, styles['CalloutText'])
    ]

    t = Table([[content]], colWidths=[PRINTABLE_WIDTH])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_col),
        ('BOX', (0, 0), (-1, -1), 1, border_col),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def code_box(title, code_str, explanation, styles):
    """Cria uma caixa estilizada para apresentar um bloco de código com explicação."""
    formatted_code = code_str.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>").replace(" ", "&nbsp;")
    code_p = Paragraph(f"<b>Arquivo: {title}</b><br/><br/><code>{formatted_code}</code>", styles['CodeSnippet'])
    expl_p = Paragraph(f"<b>O que esse trecho faz:</b> {explanation}", styles['CalloutText'])

    t = Table([[code_p], [expl_p]], colWidths=[PRINTABLE_WIDTH])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#ffffff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('LINEBELOW', (0, 0), (-1, 0), 0.8, colors.HexColor("#cbd5e1")),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def build_pdf(filename="Guia_Irrigacao_ESP32.pdf"):
    styles = get_styles()
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 12,
        bottomMargin=MARGIN + 12
    )

    story = []

    # =========================================================================
    # PÁGINA 1: CAPA DO DOCUMENTO
    # =========================================================================
    story.append(Spacer(1, 25))
    story.append(Paragraph("PROJETO DE EXTENSÃO UNIVERSITÁRIA • HORTA COMUNITÁRIA", styles['CoverBadge']))
    story.append(Spacer(1, 8))
    story.append(Paragraph("SISTEMA DE IRRIGAÇÃO AUTOMATIZADA COM ESP32", styles['CoverTitle']))
    story.append(Paragraph("Guia Didático do Firmware, Arquitetura, Pinagem e Funcionamento Passo a Passo", styles['CoverSubtitle']))

    story.append(HRFlowable(width="60%", thickness=3, color=PRIMARY, spaceBefore=0, spaceAfter=20, hAlign='CENTER'))

    cover_summary_html = (
        "<b>Para quem é este material?</b><br/>"
        "Este guia foi elaborado sob medida para estudantes, voluntários, agricultores urbanos e "
        "entusiastas que <b>não possuem familiaridade prévia com programação de microcontroladores</b> "
        "ou termos complexos de engenharia de software.<br/><br/>"
        "Aqui, cada linha de código é explicada através de analogias simples do dia a dia, e cada pino do "
        "ESP32 é apresentado com diagramas visuais e explicações práticas de onde ligar cada componente."
    )
    cover_box = Table([[Paragraph(cover_summary_html, styles['Body'])]], colWidths=[PRINTABLE_WIDTH - 20])
    cover_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#e8f5e9")),
        ('BOX', (0, 0), (-1, -1), 1.5, PRIMARY),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(cover_box)
    story.append(Spacer(1, 28))

    meta_data = [
        [Paragraph("<b>Hardware Principal:</b>", styles['TableCellBold']), Paragraph("ESP32 DevKit V1 (Dual Core 240MHz, 30 pinos)", styles['TableCell'])],
        [Paragraph("<b>Modo de Operação:</b>", styles['TableCellBold']), Paragraph("100% Offline (Rede Wi-Fi Própria / SoftAP sem necessidade de internet)", styles['TableCell'])],
        [Paragraph("<b>Linguagem e Ferramentas:</b>", styles['TableCellBold']), Paragraph("C++ moderno com Arduino Framework sob PlatformIO", styles['TableCell'])],
        [Paragraph("<b>Mecanismos de Segurança:</b>", styles['TableCellBold']), Paragraph("Cooldown (10s), Orçamento Diário (15m), Teto Máximo (5m), Parada de Emergência", styles['TableCell'])],
        [Paragraph("<b>Status da Montagem:</b>", styles['TableCellBold']), Paragraph("Fase de Mock/Testes de Bancada (LED Onboard simulando a Válvula)", styles['TableCell'])],
    ]
    meta_table = Table(meta_data, colWidths=[150, PRINTABLE_WIDTH - 170])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 35))
    story.append(Paragraph("Versão 1.0 • Documentação Técnica e Educacional Completa", styles['CoverDesc']))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: O QUE É ESTE PROJETO E DIVISÃO DE TAREFAS
    # =========================================================================
    story.append(Paragraph("1. O Que É Este Projeto e Por Que Ele Existe?", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Imagine ter uma horta comunitária em um espaço aberto, praça ou escola onde as plantas precisam "
        "de água todos os dias nos horários mais frescos (de manhã cedo e no final da tarde). Nem sempre há "
        "alguém disponível para ligar a mangueira, e muitas vezes esse local <b>não tem internet Wi-Fi</b> "
        "nem um computador por perto. Como resolver isso de forma barata, sustentável e confiável?",
        styles['Body']
    ))

    story.append(Paragraph(
        "A resposta é este projeto! Ele utiliza um chip minúsculo chamado <b>ESP32</b> para assumir o controle "
        "completo da irrigação. O projeto foi estruturado com uma premissa fundamental: <b>ele é 100% autossuficiente e offline</b>.",
        styles['Body']
    ))

    story.append(callout_box(
        "Como o sistema funciona sem internet?",
        "O ESP32 não precisa do roteador da sua casa. Ele mesmo gera a sua própria rede Wi-Fi privativa "
        "(com o nome <b>'Irrigacao-Comunitaria'</b>). Qualquer pessoa com um smartphone pode se aproximar da "
        "caixa do sistema, conectar nesse Wi-Fi e abrir o painel de controle pelo navegador de internet digitando "
        "<code>192.168.4.1</code>. Funciona até mesmo no meio de uma fazenda sem sinal de celular!",
        "tip",
        styles
    ))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Divisão de Responsabilidades no Projeto", styles['H2']))
    story.append(Paragraph(
        "Este projeto universitário foi dividido entre duas frentes de trabalho coordenadas:",
        styles['Body']
    ))

    team_data = [
        [Paragraph("Equipe de Software (Este Código)", styles['TableHeader']), Paragraph("Equipe de Montagem Física / Hidráulica", styles['TableHeader'])],
        [
            Paragraph("• Criar o cérebro lógico do sistema no ESP32.<br/>"
                      "• Gerar as páginas de controle que aparecem no celular.<br/>"
                      "• Garantir travas de segurança para nunca faltar água e nem inundar a horta.<br/>"
                      "• Guardar o histórico permanente de tudo o que aconteceu.", styles['TableCell']),
            Paragraph("• Instalar os canos de água, mangueiras gotejadoras e caixa d'água.<br/>"
                      "• Conectar a válvula solenoide (a 'torneira elétrica') à rede hidráulica.<br/>"
                      "• Fazer a ligação física dos fios na placa do ESP32.<br/>"
                      "• Acondicionar o circuito em uma caixa estanque contra chuva e poeira.", styles['TableCell'])
        ]
    ]
    t_team = Table(team_data, colWidths=[PRINTABLE_WIDTH / 2, PRINTABLE_WIDTH / 2], repeatRows=1)
    t_team.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_team)
    story.append(Spacer(1, 10))

    story.append(callout_box(
        "Autonomia e Resiliência",
        "Por rodar 100% no ESP32, se faltar luz na horta, o sistema não desconfigura. Ao retornar a energia, "
        "o chip religa automaticamente, reconstrói o Wi-Fi e retoma o monitoramento da horta sem intervenção humana.",
        "analogy",
        styles
    ))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 3: DICIONÁRIO DESCOMPLICADO DO ESP32
    # =========================================================================
    story.append(Paragraph("2. Dicionário Descomplicado: Decodificando as Nomenclaturas", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "A programação de microcontroladores é repleta de termos técnicos em inglês. "
        "A tabela abaixo traduz cada conceito para termos claros e analogias práticas do nosso dia a dia:",
        styles['Body']
    ))

    terms = [
        ("ESP32", "O Cérebro Eletrônico", "Placa compacta com processador veloz, memória e antena de rádio (Wi-Fi e Bluetooth) embutidos em um único chip. Custa barato e consome pouquíssima energia."),
        ("Firmware", "O Software de Fábrica", "Diferente de um programa de computador comum instalado no Windows, o firmware é gravado na 'alma' do chip. Ao ligar na tomada, ele já acorda rodando esse código."),
        ("GPIO (General Purpose I/O)", "Pinos de Entrada e Saída", "Perninhas metálicas da placa. Servem como 'dedos' para ligar coisas (Saída: manda energia para o relé abrir a água) ou como 'olhos' para ler dados (Entrada: mede a umidade)."),
        ("HIGH e LOW", "Ligado e Desligado", "Na eletrônica digital, tudo é 0 ou 1. <b>HIGH</b> significa colocar energia no pino (3.3V, ativando a válvula). <b>LOW</b> significa desligar a energia (0V, fechando a torneira)."),
        ("SoftAP (Ponto de Acesso)", "Roteador Próprio", "Em vez de conectar em uma rede externa, o próprio ESP32 se transforma em um roteador sem fio, permitindo que o celular se conecte diretamente nele."),
        ("SPIFFS / Flash", "O Pen Drive Interno", "Área de memória permanente dentro do ESP32. Se faltar luz ou o sistema reiniciar, as configurações salvas e o histórico de regas continuam intactos."),
        ("Mock (Simulação)", "O Dublê de Testes", "Enquanto a válvula hidráulica não chega, o código acende o LED azul da própria placa (GPIO 2) para provar visualmente que o acionamento funciona."),
        ("RTC (Real Time Clock)", "O Relógio de Bateria", "Pequeno módulo acessório com bateria tipo moeda (DS3231). Mantém a hora e os minutos correndo certinho mesmo com o ESP32 desligado da tomada."),
        ("millis() vs. delay()", "Cronômetro x Cochilo", "<code>delay(1000)</code> faz o processador dormir por 1 segundo travando tudo (ele para de responder o Wi-Fi). Já <code>millis()</code> funciona como um cronômetro: o processador checa o tempo sem parar de atender o usuário."),
        ("PlatformIO", "O Mecânico de Build", "Ferramenta moderna de desenvolvimento que substitui a antiga Arduino IDE. Baixa as bibliotecas sozinho e organiza a compilação com estabilidade profissional."),
    ]

    terms_data = [[Paragraph("Termo Técnico", styles['TableHeader']), Paragraph("Nome Amigável", styles['TableHeader']), Paragraph("O que significa na prática?", styles['TableHeader'])]]
    for term, friendly, desc in terms:
        terms_data.append([
            Paragraph(f"<b>{term}</b>", styles['TableCellBold']),
            Paragraph(friendly, styles['TableCell']),
            Paragraph(desc, styles['TableCell'])
        ])

    t_terms = Table(terms_data, colWidths=[105, 105, PRINTABLE_WIDTH - 210], repeatRows=1)
    t_terms.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_terms)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 4: DIAGRAMA DE PINAGEM DO ESP32
    # =========================================================================
    story.append(Paragraph("3. Diagrama de Pinagem do ESP32 DevKit V1", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "O ESP32 DevKit V1 de 30 pinos concentra toda a conectividade do projeto. A figura abaixo identifica "
        "cada terminal, destacando em cores vivas os pinos utilizados no firmware e as portas reservadas para expansão:",
        styles['Body']
    ))

    pinout_img_path = "docs/assets/esp32_pinout.png"
    if os.path.exists(pinout_img_path):
        story.append(Image(pinout_img_path, width=PRINTABLE_WIDTH, height=355))
        story.append(Paragraph("<b>Figura 1:</b> Diagrama de pinagem do ESP32 DevKit V1 (30 pinos) com identificação das funções do projeto.", styles['Caption']))

    story.append(Paragraph("Resumo Rápido dos Pinos Utilizados:", styles['H2']))

    pins_summary_short = [
        ("GPIO 2 (D2)", "Azul", "Válvula / LED Onboard", "Ativa o relé que abre a válvula (atualmente acende o LED azul)."),
        ("GPIO 21 (SDA)", "Roxo", "Dados I2C (RTC)", "Linha de comunicação de dados com o relógio de precisão DS3231."),
        ("GPIO 22 (SCL)", "Roxo", "Clock I2C (RTC)", "Linha de sincronismo de relógio com o módulo DS3231."),
        ("GPIO 36 (VP)", "Verde Petróleo", "Sensor Umidade (ADC)", "Entrada analógica reservada para leitura capacitiva do solo."),
        ("VIN (5V) e GND", "Vermelho/Preto", "Alimentação Principal", "Entrada de 5V da fonte e retorno negativo comum de corrente."),
    ]
    p_short_data = [[Paragraph("Pino", styles['TableHeader']), Paragraph("Cor", styles['TableHeader']), Paragraph("Função", styles['TableHeader']), Paragraph("Descrição", styles['TableHeader'])]]
    for p, c, f, d in pins_summary_short:
        p_short_data.append([
            Paragraph(f"<b>{p}</b>", styles['TableCellBold']),
            Paragraph(c, styles['TableCell']),
            Paragraph(f"<b>{f}</b>", styles['TableCell']),
            Paragraph(d, styles['TableCell'])
        ])
    t_pshort = Table(p_short_data, colWidths=[85, 75, 125, PRINTABLE_WIDTH - 285], repeatRows=1)
    t_pshort.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_pshort)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 5: ESQUEMA ELÉTRICO COMPLETO
    # =========================================================================
    story.append(Paragraph("Esquema Elétrico Didático do Sistema Completo", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Abaixo está o esquema elétrico de fácil compreensão que a equipe de montagem física utilizará "
        "para interligar a placa aos componentes reais na caixa de controle:",
        styles['Body']
    ))

    circuit_img_path = "docs/assets/circuit_diagram.png"
    if os.path.exists(circuit_img_path):
        story.append(Image(circuit_img_path, width=PRINTABLE_WIDTH, height=335))
        story.append(Paragraph("<b>Figura 2:</b> Esquema de interligação dos módulos (Relé 5V, Válvula 12V, RTC DS3231, Sensor e Fonte).", styles['Caption']))

    story.append(callout_box(
        "Por que precisamos de um Módulo Relé para acionar a válvula?",
        "O ESP32 é um processador que trabalha com níveis lógicos delicados: seus pinos fornecem apenas "
        "3.3 Volts e corrente baixíssima (cerca de 20 a 40 miliamperes). As válvulas solenoide de água exigem "
        "12 Volts e correntes elevadas para puxar o êmbolo hidráulico. Ligar a válvula diretamente no pino do ESP32 "
        "destruiria o chip na hora! O <b>Módulo Relé</b> atua como uma ponte segura: o ESP32 envia uma ordem "
        "de baixa voltagem e o relé chaveia a linha de alta voltagem com isolamento galvânico total.",
        "tip",
        styles
    ))

    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Regra de Ouro da Eletrônica: O Terra Comum (GND)</b><br/>"
        "Mesmo que a válvula use uma fonte de 12V e o ESP32 seja alimentado em 5V, o terminal <b>GND</b> "
        "de todas as placas e sensores deve ser conectado junto. O GND é o ponto de referência zero para que "
        "os sinais elétricos sejam interpretados corretamente por todos os chips.",
        styles['Body']
    ))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 6: ARQUITETURA SISTÊMICA (VISÃO GERAL)
    # =========================================================================
    story.append(Paragraph("4. Arquitetura Geral do Sistema (Visão Sistêmica)", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Um software bem estruturado é organizado em blocos funcionais independentes. "
        "A imagem a seguir sintetiza a rota da informação, desde o celular do hortelão até o acionamento físico da água:",
        styles['Body']
    ))

    arch_img_path = "docs/assets/system_architecture.png"
    if os.path.exists(arch_img_path):
        story.append(Image(arch_img_path, width=PRINTABLE_WIDTH, height=335))
        story.append(Paragraph("<b>Figura 3:</b> Arquitetura em camadas do sistema offline (Usuário -> Firmware ESP32 -> Periféricos).", styles['Caption']))

    story.append(Paragraph("Entendendo as Três Camadas do Sistema:", styles['H2']))

    story.append(Paragraph(
        "<b>1. Camada do Usuário (Interface Humana):</b> Qualquer smartphone comum se conecta à rede Wi-Fi local "
        "<code>Irrigacao-Comunitaria</code> (senha: <code>irrigacao</code>) e abre <code>192.168.4.1</code> no navegador. "
        "Não precisa instalar nenhum aplicativo na Play Store ou Apple Store!",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>2. Camada do Firmware (Cérebro Interno):</b> Dividida em três partes:<br/>"
        "• <i>Servidor Web Assíncrono (web_server.cpp):</i> Atende as requisições HTTP sem congelar a placa.<br/>"
        "• <i>Lógica & Segurança (main.cpp e logic):</i> Compara os horários e aplica as travas de proteção.<br/>"
        "• <i>Memória Flash SPIFFS (storage.cpp):</i> Salva a programação e o histórico de forma permanente.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>3. Camada Física (Atuadores e Sensores):</b> O pino GPIO 2 comanda o relé da válvula de água. "
        "No futuro, os pinos I2C lerão o RTC DS3231 e o pino ADC 36 medirá a umidade do solo.",
        styles['Body']
    ))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 7: RAIO-X DOS CÓDIGOS (PARTE 1)
    # =========================================================================
    story.append(Paragraph("5. Raio-X dos Códigos-Fonte (Parte 1: Estrutura Geral)", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "A pasta do projeto contém códigos modulares escritos em C++ moderno para a plataforma Arduino/ESP32. "
        "Vejamos o inventário completo dos arquivos e a responsabilidade de cada um:",
        styles['Body']
    ))

    files_summary = [
        ("platformio.ini", "Configuração de Build", "Diz ao compilador qual placa usar (esp32dev), a velocidade serial (115200) e baixa as bibliotecas externas necessárias."),
        ("include/Config.h", "Contrato de Parâmetros", "Define a estrutura de dados das programações (ScheduleSlot) e as constantes fixas de segurança (cooldown, cota diária)."),
        ("include/History.h", "Contrato de Histórico", "Define a estrutura HistoryEntry e o enumerador TriggerReason (motivos de acionamento ou bloqueio de rega)."),
        ("include/Routes.h", "Contrato de URLs Web", "Centraliza todos os caminhos do servidor HTTP (/status, /admin, /admin/config, etc.) para evitar erros de digitação."),
        ("include/Storage.h", "Contrato de Persistência", "Declara as assinaturas das funções de gravação e leitura na memória flash (loadConfig, saveConfig, etc.)."),
        ("src/irrigation_logic.*", "Cérebro Matemático Puro", "Função sem hardware: compara a hora atual com os horários cadastrados e diz se deve irrigar."),
        ("src/storage.cpp", "Arquivista da Flash", "Implementa a gravação e leitura direta em binário bruto nos arquivos /config.bin e /history.bin no SPIFFS."),
        ("src/web_server.*", "Garçom e Vitrine Web", "Monta as páginas HTML/CSS inline 100% offline, valida entradas de formulários e exporta o histórico em CSV."),
        ("src/main.cpp", "Maestro Operacional", "Inicializa o ESP32 (setup), sobe o Wi-Fi SoftAP, sincroniza o relógio e executa o laço contínuo de vigilância (loop)."),
    ]

    files_table_data = [[Paragraph("Arquivo", styles['TableHeader']), Paragraph("Papel no Projeto", styles['TableHeader']), Paragraph("O que ele faz em detalhes?", styles['TableHeader'])]]
    for fn, role, desc in files_summary:
        files_table_data.append([
            Paragraph(f"<b>{fn}</b>", styles['TableCellBold']),
            Paragraph(role, styles['TableCell']),
            Paragraph(desc, styles['TableCell'])
        ])

    t_files = Table(files_table_data, colWidths=[115, 110, PRINTABLE_WIDTH - 225], repeatRows=1)
    t_files.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_files)

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Detalhamento: platformio.ini e Config.h</b>", styles['H3']))

    story.append(code_box(
        "platformio.ini",
        "[env:esp32dev]\nplatform = espressif32\nboard = esp32dev\nframework = arduino\nmonitor_speed = 115200\nlib_deps =\n    ESP32Async/ESPAsyncWebServer\n    ESP32Async/AsyncTCP\n    adafruit/RTClib",
        "Configura o ambiente para compilação no ESP32 clássico, ajusta a porta serial e baixa as bibliotecas de servidor web assíncrono e relógio RTC automaticamente.",
        styles
    ))

    story.append(Spacer(1, 6))

    story.append(code_box(
        "include/Config.h (Trecho de Segurança)",
        "constexpr uint16_t MAX_IRRIGATION_DURATION_SEC = 300; // teto máximo de 5 minutos\nconstexpr uint16_t IRRIGATION_COOLDOWN_SEC = 10;      // pausa de 10s entre acionamentos\nconstexpr uint32_t DAILY_WATER_BUDGET_SEC = 900;      // limite de 15 min de água por dia",
        "Constantes fixadas diretamente no firmware. Não podem ser alteradas por acidente pela interface web, servindo de barreira de proteção definitiva.",
        styles
    ))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 8: RAIO-X DOS CÓDIGOS (PARTE 2: LÓGICA E MEMÓRIA FLASH)
    # =========================================================================
    story.append(Paragraph("5. Raio-X dos Códigos (Parte 2: Lógica Pura e Persistência)", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "<b>A) src/irrigation_logic.cpp — A Lógica Desacoplada de Hardware</b><br/>"
        "Um princípio clássico de engenharia de software é: <i>mantenha a lógica matemática pura separada dos pinos físicos</i>. "
        "A função <code>decideIrrigation()</code> não mexe em fios nem em relés; ela apenas compara números:",
        styles['Body']
    ))

    story.append(code_box(
        "src/irrigation_logic.cpp",
        "IrrigationDecision decideIrrigation(const IrrigationConfig& config,\n                                     uint8_t currentHour,\n                                     uint8_t currentMinute) {\n    for (uint8_t i = 0; i < config.scheduleCount; i++) {\n        const ScheduleSlot& slot = config.schedules[i];\n        if (slot.enabled && slot.hour == currentHour && slot.minute == currentMinute) {\n            return {true, config.irrigationDurationSec};\n        }\n    }\n    return {false, 0};\n}",
        "A função percorre os horários agendados. Se um slot estiver ativo e a hora e minuto baterem com o relógio, ela devolve 'true' e o tempo em segundos que a água deve correr.",
        styles
    ))

    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>B) src/storage.cpp — Persistência Binária Eficiente em Flash (SPIFFS)</b><br/>"
        "Em computadores comuns, é comum salvar arquivos em JSON ou bancos de dados SQL. Porém, no ESP32, "
        "essas bibliotecas gastam muita memória RAM preciosa. O projeto utiliza uma estratégia genial: "
        "<b>salvar estruturas C++ em bytes crus (binário)</b>:",
        styles['Body']
    ))

    story.append(code_box(
        "src/storage.cpp (Gravação Direta de Structs)",
        "bool saveConfig(const IrrigationConfig& config) {\n    File file = SPIFFS.open(CONFIG_PATH, FILE_WRITE);\n    size_t written = file.write(reinterpret_cast<const uint8_t*>(&config),\n                                sizeof(IrrigationConfig));\n    file.close();\n    return written == sizeof(IrrigationConfig);\n}",
        "A função abre o arquivo '/config.bin' e grava o bloco de memória exato da estrutura IrrigationConfig de uma só vez. É ultra-rápido (frações de milissegundo) e consome zero de RAM extra.",
        styles
    ))

    story.append(Spacer(1, 8))

    story.append(callout_box(
        "O que acontece no primeiro boot do ESP32?",
        "No primeiro boot da placa recém-saída da caixa, o arquivo <code>/config.bin</code> ainda não existe. "
        "A função <code>loadConfig()</code> percebe isso automaticamente e preenche a configuração com valores seguros "
        "padrão (zero horários ativos e duração de 10 segundos para testes). Em seguida, ela formata o sistema "
        "de arquivos com <code>SPIFFS.begin(true)</code> sem apresentar erros.",
        "tip",
        styles
    ))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 9: RAIO-X DOS CÓDIGOS (PARTE 3: SERVIDOR WEB E MAESTRO)
    # =========================================================================
    story.append(Paragraph("5. Raio-X dos Códigos (Parte 3: Servidor Web e Loop Central)", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "<b>A) src/web_server.cpp — Servidor Web Responsivo e 100% Offline</b><br/>"
        "O servidor HTTP embutido atende tanto as páginas visuais em HTML para celulares quanto APIs em formato JSON. "
        "Todo o estilo CSS utiliza variáveis modernas e flexbox, renderizando perfeitamente no celular sem depender de CDN:",
        styles['Body']
    ))

    story.append(code_box(
        "src/web_server.cpp (Exportação de Histórico em CSV)",
        "server.on(AsyncURIMatcher::exact(Routes::ADMIN_HISTORY), HTTP_GET, [](AsyncWebServerRequest* request) {\n    AsyncWebServerResponse* response = request->beginResponse(200, \"text/csv\", buildHistoryCsv());\n    response->addHeader(\"Content-Disposition\", \"attachment; filename=history.csv\");\n    request->send(response);\n});",
        "Ao clicar em 'Baixar CSV', o ESP32 lê o arquivo /history.bin, traduz os timestamps para datas legíveis (ex: 24/09/2026 17:30) e envia como download direto para o navegador.",
        styles
    ))

    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>B) src/main.cpp — O Maestro do Sistema (Setup e Loop)</b><br/>"
        "O arquivo <code>main.cpp</code> conecta todas as peças. Ele é responsável pelo ciclo de vida da placa:",
        styles['Body']
    ))

    story.append(code_box(
        "src/main.cpp (Laço Principal Não-Bloqueante)",
        "void setup() {\n    pinMode(VALVE_PIN, OUTPUT);        // Configura pino GPIO 2\n    loadConfig(config);                 // Carrega agendamentos da memória\n    WiFi.softAP(AP_SSID, AP_PASSWORD); // Cria o Wi-Fi 'Irrigacao-Comunitaria'\n    server.begin();                     // Coloca o servidor web no ar\n}\n\nvoid loop() {\n    updateValve();         // Fecha a válvula se o tempo estipulado tiver passado\n    evaluateIrrigation();  // Avalia a cada 1 segundo se bateu o horário agendado\n}",
        "Perceba a ausência de delay()! A função updateValve() compara o cronômetro millis() com o tempo limite da rega, mantendo o processador 100% livre para atender os usuários no Wi-Fi.",
        styles
    ))

    story.append(Spacer(1, 8))

    story.append(callout_box(
        "Deduplicação de Minuto: Evitando Disparos Repetidos",
        "Como a função <code>evaluateIrrigation()</code> roda a cada segundo e a irrigação é programada por hora e minuto "
        "(ex: 06:30), o minuto 30 dura 60 segundos inteiros! Sem uma proteção, o sistema tentaria religar a válvula "
        "60 vezes seguidas. O código resolve isso com uma 'chave de minuto' (<code>currentMinuteKey = hour * 60 + minute</code>), "
        "garantindo que o disparo ocorra exatamente uma única vez por agendamento.",
        "analogy",
        styles
    ))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 10: ROTINAS E FILOSOFIA DE SEGURANÇA
    # =========================================================================
    story.append(Paragraph("6. Rotinas de Segurança: A Blindagem do Sistema", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Em hortas comunitárias, uma válvula travada aberta por falha de código pode esvaziar a caixa d'água "
        "ou afogar as plantações. O firmware foi construído com <b>quatro travas de segurança em cascata</b> "
        "que impedem qualquer desperdício:",
        styles['Body']
    ))

    flow_img_path = "docs/assets/safety_flowchart.png"
    if os.path.exists(flow_img_path):
        story.append(Image(flow_img_path, width=PRINTABLE_WIDTH, height=330))
        story.append(Paragraph("<b>Figura 4:</b> Fluxograma das quatro etapas de validação de segurança antes da liberação de água.", styles['Caption']))

    story.append(Paragraph("As Quatro Travas de Segurança Explicadas:", styles['H2']))

    trava_info = [
        ("Trava 1: Intervalo Mínimo (Cooldown de 10s)", "Impede acionamentos em rajada por cliques repetidos no botão web. Se a válvula acabou de fechar, aguarda no mínimo 10 segundos antes de reabrir, evitando o golpe de aríete nos canos."),
        ("Trava 2: Orçamento Diário de Água (900s / 15 min)", "Soma o tempo total de torneira aberta durante o dia. Ao atingir 15 minutos acumulados, bloqueia qualquer novo acionamento até o dia seguinte. Proteção vital contra encharcamento!"),
        ("Trava 3: Teto Absoluto por Acionamento (300s / 5 min)", "Nenhum acionamento manual ou agendado ultrapassa 5 minutos. Se o usuário digitar 9999 segundos na interface, a função openValve() poda o valor automaticamente para 300 segundos."),
        ("Trava 4: Parada de Emergência (/admin/stop)", "Botão vermelho de ação instantânea. Ao ser clicado, desliga a válvula no mesmo milissegundo e grava um registro com o motivo EMERGENCY_STOP no histórico."),
    ]

    for title, desc in trava_info:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", styles['Body']))

    story.append(Spacer(1, 4))
    story.append(callout_box(
        "Auditoria Completa de Bloqueios no Histórico",
        "Quando uma tentativa de irrigar é barrada pelas travas, o sistema grava a recusa no arquivo de histórico com o "
        "motivo exato: <code>BLOCKED_COOLDOWN</code> ou <code>BLOCKED_DAILY_BUDGET</code>. Nada ocorre de forma invisível!",
        "alert",
        styles
    ))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 11: GUIA PRÁTICO DO HORTELÃO (OPERAÇÃO E QR CODES)
    # =========================================================================
    story.append(Paragraph("7. Como Usar na Prática: Guia do Hortelão", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "A operação foi simplificada ao máximo para que qualquer pessoa consiga utilizar o sistema em campo "
        "através da câmera do celular, sem precisar digitar comandos ou instalar aplicativos:",
        styles['Body']
    ))

    qr_wifi_path = "docs/qr-wifi.png"
    qr_status_path = "docs/qr-status.png"

    if os.path.exists(qr_wifi_path) and os.path.exists(qr_status_path):
        qr_cells = [
            [Image(qr_wifi_path, width=105, height=105), Image(qr_status_path, width=105, height=105)],
            [
                Paragraph("<b>PASSO 1: Conectar ao Wi-Fi</b><br/>Aponte a câmera para conectar:<br/><b>SSID:</b> <code>Irrigacao-Comunitaria</code><br/><b>Senha:</b> <code>irrigacao</code>", styles['TableCell']),
                Paragraph("<b>PASSO 2: Abrir o Painel</b><br/>Aponte a câmera para abrir o painel:<br/><b>Endereço direto:</b><br/><code>http://192.168.4.1/status</code>", styles['TableCell'])
            ]
        ]
        t_qr = Table(qr_cells, colWidths=[PRINTABLE_WIDTH / 2, PRINTABLE_WIDTH / 2], repeatRows=1)
        t_qr.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(t_qr)
        story.append(Paragraph("<b>Figura 5:</b> QR Codes para fixação na tampa da caixa hermética da horta comunitária.", styles['Caption']))

    story.append(Paragraph("Navegação pelas Telas do Sistema:", styles['H2']))

    story.append(Paragraph(
        "<b>1. Tela de Status Geral (<code>/status</code>):</b><br/>"
        "Painel público e intuitivo. Apresenta uma luz em destaque (badge): verde (<b>'Irrigando agora'</b>) ou "
        "cinza (<b>'Aguardando'</b>). Exibe o relógio do sistema, quando foi a última rega e a lista de horários "
        "ativos. A página se atualiza sozinha a cada 5 segundos via JavaScript sem precisar recarregar o navegador.",
        styles['Body']
    ))

    story.append(Paragraph(
        "<b>2. Tela Administrativa (<code>/admin</code>):</b><br/>"
        "Painel de controle para os responsáveis pela horta. Permite:<br/>"
        "• <i>Ajustar Horário do Sistema:</i> Como ainda não há o RTC físico, use o seletor de data/hora do celular para sincronizar o relógio.<br/>"
        "• <i>Programar Agendamentos:</i> Habilita os slots de irrigação (hora e minuto) e a duração desejada.<br/>"
        "• <i>Irrigação Manual de Teste:</i> Abre a torneira sob demanda para verificar a vazão dos canos.<br/>"
        "• <i>Parada de Emergência:</i> Fecha a válvula imediatamente em caso de vazamento.<br/>"
        "• <i>Baixar Histórico em CSV:</i> Exporta o relatório completo de eventos para abrir no Microsoft Excel.",
        styles['Body']
    ))

    story.append(Spacer(1, 4))
    story.append(callout_box(
        "Atenção para a Fase de Entrega à Comunidade:",
        "Nesta fase de desenvolvimento em laboratório, a exigência de senha de acesso foi temporariamente desligada "
        "para facilitar os testes de bancada. Antes de colocar o equipamento na horta, reative a senha nas rotas <code>/admin</code> "
        "para que pessoas não autorizadas não alterem as programações.",
        "alert",
        styles
    ))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 12: DO MOCK AO REAL (ROTEIRO DE MONTAGEM)
    # =========================================================================
    story.append(Paragraph("8. Do Mock ao Hardware Real: Roteiro de Montagem", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "O firmware já está pronto e testado em bancada (com o LED azul onboard simulando a válvula). "
        "Quando a equipe de montagem física receber as peças definitivas, basta seguir este roteiro de instalação:",
        styles['Body']
    ))

    hw_steps = [
        ("Passo 1: Conexão do Módulo Relé de 5V", "Ligue o pino <b>IN</b> do relé no pino <b>GPIO 2</b> do ESP32, o <b>VCC</b> no pino <b>VIN (5V)</b> e o <b>GND</b> no <b>GND</b>. O código já aciona esse pino sem necessidade de alterar nenhuma linha de programação!"),
        ("Passo 2: Ligação da Válvula Solenoide de 12V", "A válvula possui dois polos. Interrompa o polo positivo passando pelo contato Normalmente Aberto (NA/COM) do relé e alimente pela fonte de 12V externa. Ao fechar o relé, a água corre."),
        ("Passo 3: Instalação do Relógio RTC DS3231", "Conecte o <b>VCC</b> em <b>3V3</b>, <b>GND</b> em <b>GND</b>, <b>SDA</b> no pino <b>GPIO 21</b> e <b>SCL</b> no pino <b>GPIO 22</b>. Descomente a rotina do RTC no <code>main.cpp</code>. A placa nunca mais perderá a hora ao ser desligada!"),
        ("Passo 4: Integração do Sensor de Umidade Capacitivo", "Enterre o sensor V1.2 próximo à raiz das plantas. Ligue seu <b>VCC</b> em <b>3V3</b>, <b>GND</b> em <b>GND</b> e o terminal <b>AOUT</b> no pino <b>GPIO 36 (VP)</b>."),
        ("Passo 5: Acondicionamento Hermético (Caixa IP65)", "O circuito deve ser fixado dentro de uma caixa plástica vedada com proteção IP65 (contra chuva, poeira e formigas). Os cabos devem passar por prensa-cabos emborrachados na parte inferior."),
    ]

    for p_title, p_desc in hw_steps:
        story.append(Paragraph(f"• <b>{p_title}:</b> {p_desc}", styles['Body']))
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Checklist de Validação Física Antes de Ligar a Água:", styles['H2']))

    chk_data = [
        [Paragraph("Item a Verificar", styles['TableHeader']), Paragraph("Critério de Aceite", styles['TableHeader']), Paragraph("Status", styles['TableHeader'])],
        [Paragraph("Terra Comum (GND)", styles['TableCellBold']), Paragraph("GND da fonte 12V, do ESP32 e dos módulos conectados juntos.", styles['TableCell']), Paragraph("[  ] OK", styles['TableCellBold'])],
        [Paragraph("Tensão no ESP32", styles['TableCellBold']), Paragraph("Medir 5V estáveis no pino VIN e 3.3V no pino 3V3 com multímetro.", styles['TableCell']), Paragraph("[  ] OK", styles['TableCellBold'])],
        [Paragraph("Sentido da Válvula", styles['TableCellBold']), Paragraph("A seta de fluxo no corpo da solenoide aponta para a horta.", styles['TableCell']), Paragraph("[  ] OK", styles['TableCellBold'])],
        [Paragraph("Estanqueidade", styles['TableCellBold']), Paragraph("Abrir o registro de água com relé desligado: vazamento zero.", styles['TableCell']), Paragraph("[  ] OK", styles['TableCellBold'])],
        [Paragraph("Acionamento Manual", styles['TableCellBold']), Paragraph("Clicar em 'Irrigar agora' via celular: relé atraca e água sai.", styles['TableCell']), Paragraph("[  ] OK", styles['TableCellBold'])],
    ]
    t_chk = Table(chk_data, colWidths=[130, PRINTABLE_WIDTH - 210, 80], repeatRows=1)
    t_chk.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_chk)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 13: PERGUNTAS FREQUENTES E FICHA TÉCNICA DE BOLSO
    # =========================================================================
    story.append(Paragraph("9. Resolução de Dúvidas e Ficha Técnica de Bolso", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    faqs = [
        ("O ESP32 perdeu as horas depois que faltou luz. O que aconteceu?",
         "Nesta fase de bancada, o relógio externo de bateria (RTC) ainda não foi conectado. O horário fica guardado na memória RAM. Ao ligar, basta conectar pelo celular em <code>/admin</code> e salvar o horário atual."),
        ("Estou longe da horta e não encontro o Wi-Fi. Qual o alcance do sinal?",
         "A antena compacta do ESP32 alcança de 15 a 30 metros em linha reta. É necessário se aproximar da caixa da horta para estabelecer conexão com o painel."),
        ("Apareceu 'Falha detectada' em vermelho na tela de status. O que significa?",
         "Indica que a gravação na memória SPIFFS falhou (memória corrompida). Basta regravar a partição do sistema de arquivos via <code>pio run -t uploadfs</code>."),
    ]

    for q, a in faqs:
        story.append(Paragraph(f"<b>P: {q}</b>", styles['BodyBold']))
        story.append(Paragraph(f"<b>R:</b> {a}", styles['Body']))
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Ficha Técnica de Bolso (Guarde com o Equipamento)", styles['H2']))

    pocket_card_data = [
        [Paragraph("Rede Wi-Fi (SSID):", styles['TableCellBold']), Paragraph("<code>Irrigacao-Comunitaria</code>", styles['TableCell'])],
        [Paragraph("Senha do Wi-Fi:", styles['TableCellBold']), Paragraph("<code>irrigacao</code>", styles['TableCell'])],
        [Paragraph("Endereço no Navegador:", styles['TableCellBold']), Paragraph("<code>http://192.168.4.1/status</code> (Público) | <code>http://192.168.4.1/admin</code> (Config)", styles['TableCell'])],
        [Paragraph("Pino da Válvula (Sinal):", styles['TableCellBold']), Paragraph("GPIO 2 (Ativo em nível HIGH / 3.3V)", styles['TableCell'])],
        [Paragraph("Pinos do Relógio RTC DS3231:", styles['TableCellBold']), Paragraph("GPIO 21 (SDA) e GPIO 22 (SCL) via I2C", styles['TableCell'])],
        [Paragraph("Pino do Sensor de Umidade:", styles['TableCellBold']), Paragraph("GPIO 36 / VP (Leitura Analógica de 0 a 4095)", styles['TableCell'])],
        [Paragraph("Limites de Segurança:", styles['TableCellBold']), Paragraph("Cooldown: 10s | Orçamento Diário: 15 min (900s) | Teto Máximo: 5 min (300s)", styles['TableCell'])],
        [Paragraph("Comandos de Gravação (PlatformIO):", styles['TableCellBold']), Paragraph("<code>pio run</code> (Compilar) | <code>pio run -t upload</code> (Gravar) | <code>pio run -t uploadfs</code> (Limpar Flash)", styles['TableCell'])],
    ]
    t_pocket = Table(pocket_card_data, colWidths=[150, PRINTABLE_WIDTH - 150], repeatRows=1)
    t_pocket.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1.2, PRIMARY),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_pocket)

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=4, spaceAfter=8))
    story.append(Paragraph(
        "<i>Documentação técnica e didática desenvolvida para o Projeto de Extensão Universitária — Horta Comunitária Inteligente. "
        "Código-fonte sob licença livre e colaborativa. Todos os direitos reservados à equipe do projeto.</i>",
        styles['Caption']
    ))

    # Constrói o documento utilizando o NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Sucesso! Documento gerado em: {filename}")


if __name__ == "__main__":
    build_pdf("Guia_Irrigacao_ESP32.pdf")
