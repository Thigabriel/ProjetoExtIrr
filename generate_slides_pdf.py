"""
Script gerador da Apresentação em Slides (PDF 16:9 Widescreen):
Versão Otimizada e Resumida (7 Slides Focados na Arquitetura de Segurança e Teoria Operacional)
Garante proporção exata para todas as imagens (sem distorções/esticamentos).
"""

import os
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.pdfgen import canvas

SLIDE_WIDTH = 960
SLIDE_HEIGHT = 540
MARGIN = 40
USABLE_WIDTH = SLIDE_WIDTH - 2 * MARGIN
USABLE_HEIGHT = SLIDE_HEIGHT - 2 * MARGIN

# Paleta de Cores da Apresentação
DARK_BG = colors.HexColor("#0f172a")
PRIMARY_GREEN = colors.HexColor("#1b4332")
EMERALD = colors.HexColor("#2d6a4f")
MINT = colors.HexColor("#52b788")
TEXT_DARK = colors.HexColor("#1e293b")
MUTED_TEXT = colors.HexColor("#64748b")
CARD_BG = colors.HexColor("#f8fafc")
CARD_BORDER = colors.HexColor("#e2e8f0")
ALERT_RED = colors.HexColor("#b91c1c")
ALERT_BG = colors.HexColor("#fef2f2")
ALERT_BORDER = colors.HexColor("#fca5a5")
NOTE_BLUE = colors.HexColor("#1d4ed8")
NOTE_BG = colors.HexColor("#eff6ff")
AMBER = colors.HexColor("#b45309")


def make_proportional_image(image_path, max_width, max_height, h_align='CENTER'):
    """
    Carrega a imagem com PIL para obter suas dimensões originais e
    calcula largura e altura preservando rigorosamente o aspect ratio,
    impedindo qualquer deformação ou esticamento visual.
    """
    if not os.path.exists(image_path):
        return Paragraph(f"<i>Imagem não encontrada: {image_path}</i>", ParagraphStyle('MissingImg', fontName='Helvetica', fontSize=8, textColor=ALERT_RED))

    with PILImage.open(image_path) as im:
        orig_w, orig_h = im.size

    aspect = orig_w / orig_h

    # Tenta encaixar pela largura máxima
    w = max_width
    h = w / aspect

    # Se ultrapassar a altura máxima permitida, restringe pela altura
    if h > max_height:
        h = max_height
        w = h * aspect

    img = Image(image_path, width=w, height=h)
    img.hAlign = h_align
    return img


def draw_cover_background(c, doc):
    """Desenha o fundo escuro da capa ANTES do texto ser renderizado."""
    c.saveState()
    c.setFillColor(colors.HexColor("#0f291e"))
    c.rect(0, 0, SLIDE_WIDTH, SLIDE_HEIGHT, fill=True, stroke=False)
    # Faixa verde menta no topo
    c.setFillColor(MINT)
    c.rect(0, SLIDE_HEIGHT - 8, SLIDE_WIDTH, 8, fill=True, stroke=False)
    # Linha no rodapé da capa
    c.setFillColor(EMERALD)
    c.rect(0, 0, SLIDE_WIDTH, 4, fill=True, stroke=False)
    c.restoreState()


class SlideCanvas(canvas.Canvas):
    """Canvas para slides 16:9 com cabeçalho de seção e rodapé numerado dinamicamente."""
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
            self.draw_slide_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_slide_decorations(self, total_pages):
        # Na Capa (Slide 1), o fundo já foi pintado
        if self._pageNumber == 1:
            return

        self.saveState()
        # Barra superior decorativa
        self.setFillColor(EMERALD)
        self.rect(0, SLIDE_HEIGHT - 6, SLIDE_WIDTH, 6, fill=True, stroke=False)

        # Cabeçalho do slide
        self.setFont("Helvetica-Bold", 8.5)
        self.setFillColor(EMERALD)
        self.drawString(MARGIN, SLIDE_HEIGHT - 22, "PROJETO DE EXTENSÃO UNIVERSITÁRIA • IRRIGAÇÃO AUTOMATIZADA ESP32")
        self.setFont("Helvetica", 8.5)
        self.setFillColor(MUTED_TEXT)
        self.drawRightString(SLIDE_WIDTH - MARGIN, SLIDE_HEIGHT - 22, "ARQUITETURA DE SEGURANÇA E CONFIABILIDADE")

        self.setStrokeColor(CARD_BORDER)
        self.setLineWidth(0.8)
        self.line(MARGIN, SLIDE_HEIGHT - 28, SLIDE_WIDTH - MARGIN, SLIDE_HEIGHT - 28)

        # Rodapé do slide
        self.line(MARGIN, 26, SLIDE_WIDTH - MARGIN, 26)
        self.drawString(MARGIN, 14, "Mecanismos de Segurança, Confiabilidade e Tolerância a Falhas em Ambiente Offline")
        self.drawRightString(SLIDE_WIDTH - MARGIN, 14, f"Slide {self._pageNumber} de {total_pages}")
        self.restoreState()


def get_styles():
    base = getSampleStyleSheet()
    styles = {
        'CoverPill': ParagraphStyle(
            'CoverPill',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=MINT,
            alignment=1,
            spaceAfter=15
        ),
        'CoverTitle': ParagraphStyle(
            'CoverTitle',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=27,
            leading=33,
            textColor=colors.white,
            alignment=1,
            spaceAfter=14
        ),
        'CoverSubtitle': ParagraphStyle(
            'CoverSubtitle',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=13.5,
            leading=18,
            textColor=colors.HexColor("#d1fae5"),
            alignment=1,
            spaceAfter=28
        ),
        'CoverMeta': ParagraphStyle(
            'CoverMeta',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#a7f3d0"),
            alignment=1
        ),
        'SlideTitle': ParagraphStyle(
            'SlideTitle',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=17,
            leading=21,
            textColor=PRIMARY_GREEN,
            spaceBefore=0,
            spaceAfter=3
        ),
        'SlideSubtitle': ParagraphStyle(
            'SlideSubtitle',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=13.5,
            textColor=MUTED_TEXT,
            spaceAfter=10
        ),
        'CardTitle': ParagraphStyle(
            'CardTitle',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=PRIMARY_GREEN,
            spaceAfter=4
        ),
        'CardTitleRed': ParagraphStyle(
            'CardTitleRed',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=ALERT_RED,
            spaceAfter=4
        ),
        'CardTitleBlue': ParagraphStyle(
            'CardTitleBlue',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=NOTE_BLUE,
            spaceAfter=4
        ),
        'CardTitleAmber': ParagraphStyle(
            'CardTitleAmber',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=AMBER,
            spaceAfter=4
        ),
        'CardText': ParagraphStyle(
            'CardText',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=TEXT_DARK
        ),
        'MetricValue': ParagraphStyle(
            'MetricValue',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=EMERALD,
            alignment=1
        ),
        'MetricLabel': ParagraphStyle(
            'MetricLabel',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=MUTED_TEXT,
            alignment=1
        ),
        'TableHeader': ParagraphStyle(
            'TableHeader',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
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
            textColor=PRIMARY_GREEN
        ),
    }
    return styles


def make_card(title, text, styles, width=430, is_alert=False, border_col=None, bg_col=None, title_style='CardTitle'):
    b_col = ALERT_BORDER if is_alert else (border_col or CARD_BORDER)
    bg = ALERT_BG if is_alert else (bg_col or CARD_BG)
    t_style = styles['CardTitleRed'] if is_alert else styles.get(title_style, styles['CardTitle'])

    content = [
        Paragraph(title, t_style),
        Spacer(1, 2),
        Paragraph(text, styles['CardText'])
    ]
    t = Table([[content]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 1.2, b_col),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def build_slides_pdf(filename="Apresentacao_Seguranca_ESP32.pdf"):
    styles = get_styles()
    doc = SimpleDocTemplate(
        filename,
        pagesize=(SLIDE_WIDTH, SLIDE_HEIGHT),
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=25,
        bottomMargin=25
    )

    story = []

    # =========================================================================
    # SLIDE 1: CAPA DA APRESENTAÇÃO
    # =========================================================================
    story.append(Spacer(1, 45))
    story.append(Paragraph("PROJETO DE EXTENSÃO UNIVERSITÁRIA • HORTA COMUNITÁRIA INTELIGENTE", styles['CoverPill']))
    story.append(Spacer(1, 10))
    story.append(Paragraph("ARQUITETURA DE SEGURANÇA E CONFIABILIDADE<br/>NO FIRMWARE ESP32", styles['CoverTitle']))
    story.append(Paragraph("Mecanismos de Proteção Ativa, Travas Hidráulicas e Tolerância a Falhas em Ambiente Offline", styles['CoverSubtitle']))

    story.append(Spacer(1, 30))
    meta_html = (
        "<b>Equipe de Software & Firmware:</b> Desenvolvimento C++ / Arduino / PlatformIO<br/>"
        "<b>Foco da Sessão:</b> Defesa em Profundidade, Fluxogramas Operacionais e Travas Hidráulicas<br/>"
        "<b>Ambiente:</b> 100% Desconectado (Sem Dependência de Servidores em Nuvem)"
    )
    story.append(Paragraph(meta_html, styles['CoverMeta']))
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 2: CONTEXTO DA HORTA E ARQUITETURA DE DEFESA EM PROFUNDIDADE
    # =========================================================================
    story.append(Paragraph("Contexto Operacional e Defesa em Profundidade", styles['SlideTitle']))
    story.append(Paragraph("Como uma arquitetura de segurança em 4 camadas protege a horta contra falhas físicas e operacionais", styles['SlideSubtitle']))

    # Imagem proporcional de Defesa em Profundidade
    did_img = make_proportional_image("docs/assets/defense_in_depth.png", max_width=510, max_height=360)

    side_card1 = make_card(
        "⚠️ O Desafio da Horta Comunitária",
        "• <b>Operação Desassistida:</b> O equipamento opera ao ar livre sem supervisão contínua.<br/>"
        "• <b>Ausência de Internet/Nuvem:</b> Não há envio de notificações de emergência por e-mail ou WhatsApp.<br/>"
        "• <b>Ameaças Reais Mitigadas:</b> Inundação dos canteiros por válvula aberta, ruptura de canos de PVC por choque hidráulico (golpe de aríete) e esvaziamento prematuro da caixa d'água.",
        styles, width=355, is_alert=True
    )
    side_card2 = make_card(
        "🛡️ Filosofia Fail-Secure (Bloqueio por Padrão)",
        "O firmware foi projetado como a <b>barreira intransponível</b> do projeto:<br/>"
        "• Nenhuma ordem de rega chega ao pino do atuador sem passar por <b>4 portões sequenciais</b>.<br/>"
        "• Em caso de dúvida, inconsistência de horário ou estouro de cota, o sistema <b>rejeita a abertura</b> e audita a recusa.",
        styles, width=355, border_col=EMERALD, bg_col=colors.HexColor("#f0fdf4")
    )
    col_text2 = [side_card1, Spacer(1, 8), side_card2]

    t_s2 = Table([[did_img, col_text2]], colWidths=[515, 365])
    t_s2.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_s2)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 3: FLUXOGRAMA DE DECISÃO (SAFETY GATES)
    # =========================================================================
    story.append(Paragraph("Fluxograma Central de Tomada de Decisão", styles['SlideTitle']))
    story.append(Paragraph("Rastreabilidade do pipeline de validação lógica percorrido por cada solicitação de água", styles['SlideSubtitle']))

    # Imagem proporcional do Fluxograma
    flow_img = make_proportional_image("docs/assets/safety_flowchart.png", max_width=450, max_height=360)

    f_card1 = make_card(
        "🎯 Ponto Único de Decisão (attemptIrrigation)",
        "Tanto a rega programada pelo relógio RTC quanto o acionamento manual sob demanda via interface web passam <b>obrigatoriamente pelo mesmo funil de validação</b>. "
        "Não existem atalhos ou acessos diretos ao pino físico.",
        styles, width=410, border_col=NOTE_BLUE, bg_col=NOTE_BG, title_style='CardTitleBlue'
    )
    f_card2 = make_card(
        "🔍 Os 4 Portões Sequenciais de Avaliação",
        "<b>1. Estado & Cooldown:</b> A válvula já está aberta? Faz menos de 10s que fechou? Se sim, rejeita imediatamente.<br/>"
        "<b>2. Orçamento Diário:</b> A soma do consumo de hoje com a nova duração ultrapassa 900s? Se sim, bloqueia.<br/>"
        "<b>3. Poda Unitária:</b> O tempo solicitado excede 300s? Se sim, é truncado automaticamente para 5 min.<br/>"
        "<b>4. Ativação Física:</b> Somente após todos os 'OK', o pino GPIO 2 recebe sinal HIGH.",
        styles, width=410, border_col=CARD_BORDER, bg_col=CARD_BG
    )
    f_card3 = make_card(
        "🚨 Canal Prioritário de Parada de Emergência",
        "O botão <code>/admin/stop</code> opera fora da fila regular: envia nível LOW para o pino em menos de 1 milissegundo e grava auditoria de emergência.",
        styles, width=410, is_alert=True
    )
    col_text3 = [f_card1, Spacer(1, 6), f_card2, Spacer(1, 6), f_card3]

    t_s3 = Table([[flow_img, col_text3]], colWidths=[460, 420])
    t_s3.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_s3)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 4: AS 4 TRAVAS DE SEGURANÇA OPERACIONAL (TEORIA E PARÂMETROS)
    # =========================================================================
    story.append(Paragraph("As 4 Travas de Segurança Operacional no Firmware", styles['SlideTitle']))
    story.append(Paragraph("Fundamentos físicos, parâmetros de projeto e comportamento defensivo do sistema", styles['SlideSubtitle']))

    t1_card = make_card(
        "⏱️ Trava 1: Cooldown de 10 Segundos",
        "• <b>Fundamento Físico:</b> O fechamento brusco de solenoides gera pico violento de pressão (<b>golpe de aríete</b>), rompendo conexões de PVC e sobreaquecendo a bobina magnética.<br/>"
        "• <b>Comportamento:</b> Impõe repouso obrigatório de 10s após cada término. Filtra cliques repetidos e afobados na interface web.<br/>"
        "• <b>Auditoria:</b> Rejeição instantânea com registro de <code>BLOCKED_COOLDOWN</code>.",
        styles, width=425, border_col=AMBER, bg_col=colors.HexColor("#fffbeb"), title_style='CardTitleAmber'
    )
    t2_card = make_card(
        "💧 Trava 2: Orçamento Diário (900s / 15 min)",
        "• <b>Fundamento Físico:</b> Garante que o reservatório de água nunca seja esvaziado e impede o afogamento de raízes das mudas na fase sem sensor de umidade.<br/>"
        "• <b>Comportamento:</b> Rastreia o consumo acumulado no dia solar. Se nova duração + consumo > 900s, o acionamento é barrado.<br/>"
        "• <b>Auditoria:</b> Bloqueio até a meia-noite com código <code>BLOCKED_DAILY_BUDGET</code>.",
        styles, width=425, border_col=EMERALD, bg_col=colors.HexColor("#f0fdf4")
    )
    t3_card = make_card(
        "🛡️ Trava 3: Teto Absoluto por Acionamento (300s)",
        "• <b>Fundamento Físico:</b> Protege contra erros humanos de digitação no formulário web (ex: digitar 9999s) ou valores corrompidos na memória flash.<br/>"
        "• <b>Comportamento:</b> Poda sumária para no máximo <b>5 minutos (300s)</b> antes de qualquer acionamento do atuador.<br/>"
        "• <b>Garantia:</b> Nenhuma rega individual ultrapassa 300 segundos.",
        styles, width=425, border_col=NOTE_BLUE, bg_col=NOTE_BG, title_style='CardTitleBlue'
    )
    t4_card = make_card(
        "🚨 Trava 4: Parada de Emergência Imediata",
        "• <b>Fundamento Físico:</b> Intervenção crítica caso uma mangueira se solte, um cano se rompa ou ocorra vazamento visível durante a operação.<br/>"
        "• <b>Comportamento:</b> Endpoint dedicado <code>POST /admin/stop</code> que zera o pino da válvula para nível LOW em menos de 1 milissegundo.<br/>"
        "• <b>Auditoria:</b> Interrupção gravada permanentemente com o código <code>EMERGENCY_STOP</code>.",
        styles, width=425, is_alert=True
    )

    t_s4 = Table([[t1_card, t2_card], [t3_card, t4_card]], colWidths=[440, 440])
    t_s4.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_s4)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 5: SIMULAÇÃO PRÁTICA DO ORÇAMENTO DIÁRIO (TIMELINE 24H)
    # =========================================================================
    story.append(Paragraph("Simulação Prática: Orçamento Diário de Água em 24h", styles['SlideTitle']))
    story.append(Paragraph("Como o firmware monitora a cota cumulativa e bloqueia tentativas que ultrapassam o limite seguro", styles['SlideSubtitle']))

    # Imagem proporcional do Timeline de Orçamento Diário
    timeline_img = make_proportional_image("docs/assets/budget_timeline.png", max_width=510, max_height=360)

    time_card1 = make_card(
        "📊 O Ciclo Normal de 3 Regas Diárias",
        "• <b>06:30 (Rega Matinal):</b> 300s executados (Acumulado: 300s).<br/>"
        "• <b>12:00 (Rega do Meio-Dia):</b> 300s executados (Acumulado: 600s).<br/>"
        "• <b>17:30 (Rega Vespertina):</b> 300s executados (Acumulado: 900s).<br/>"
        "Neste momento, a cota de 15 minutos foi <b>100% atingida</b>.",
        styles, width=355, border_col=EMERALD, bg_col=colors.HexColor("#f0fdf4")
    )
    time_card2 = make_card(
        "🚫 Cenário Crítico: 4ª Tentativa às 19:00",
        "Um voluntário clica na interface web pedindo 120s de irrigação:<br/>"
        "• <b>Cálculo do Firmware:</b> 900s (já gastos) + 120s = 1020s &gt; 900s.<br/>"
        "• <b>Ação do Sistema:</b> Abertura <b>rejeitada instantaneamente</b>.<br/>"
        "• <b>Feedback:</b> Tarja vermelha na tela web e gravação no histórico sob o código <code>BLOCKED_DAILY_BUDGET</code>.",
        styles, width=355, is_alert=True
    )
    time_card3 = make_card(
        "🔄 Reinício Solar Automático (Sem Nuvem)",
        "O ESP32 calcula o índice solar diário: <code>dayIndex = tempo / 86400L</code>. "
        "Exatamente às 00:00 da meia-noite, o índice avança e o contador diário é zerado para 0s de forma 100% autônoma.",
        styles, width=355, border_col=NOTE_BLUE, bg_col=NOTE_BG, title_style='CardTitleBlue'
    )
    col_text5 = [time_card1, Spacer(1, 6), time_card2, Spacer(1, 6), time_card3]

    t_s5 = Table([[timeline_img, col_text5]], colWidths=[515, 365])
    t_s5.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_s5)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 6: CONFIABILIDADE TEMPORAL, MEMÓRIA E AUDITORIA
    # =========================================================================
    story.append(Paragraph("Confiabilidade Temporal, Memória e Rastreabilidade", styles['SlideTitle']))
    story.append(Paragraph("Tratamento rigoroso de tempo e persistência não-volátil em ambiente desconectado", styles['SlideSubtitle']))

    r1_card = make_card(
        "⏱️ RTC DS3231 & Deduplicação de Minuto",
        "• <b>Relógio com Bateria de Lítio:</b> Preserva a data e hora mesmo se faltar energia na horta comunitária.<br/>"
        "• <b>Anti-Spam de Laço:</b> O laço <code>loop()</code> roda a cada 1s. Como o minuto dura 60s, o firmware gera uma chave temporal única (<code>hora * 60 + minuto</code>). Disparos adicionais no mesmo minuto são ignorados, garantindo <b>exatamente 1 acionamento</b>.",
        styles, width=280, border_col=NOTE_BLUE, bg_col=CARD_BG, title_style='CardTitleBlue'
    )
    r2_card = make_card(
        "📅 Validação Estrita de Calendário",
        "• <b>Prevenção de Estouro em C:</b> A função padrão <code>mktime()</code> converteria silenciosamente '31 de fevereiro' em '3 de março'.<br/>"
        "• <b>Verificação Manual:</b> O firmware implementa validador de dias por mês (1 a 31) com algoritmo de anos bissextos em <code>isValidCalendarDateTime()</code>, rejeitando dados anômalos com HTTP 400.",
        styles, width=280, border_col=AMBER, bg_col=CARD_BG, title_style='CardTitleAmber'
    )
    r3_card = make_card(
        "💾 Flash SPIFFS & Alerta de Memória",
        "• <b>Gravação Binária Compacta:</b> Histórico e horários gravados diretamente na memória flash interna.<br/>"
        "• <b>Diagnóstico de Falha:</b> Se o chip flash falhar na escrita, a variável global <code>storageFault</code> ativa um alerta vermelho permanente no dashboard <code>/status</code>, orientando a equipe a acionar o suporte.",
        styles, width=280, is_alert=True
    )

    t_s6_top = Table([[r1_card, r2_card, r3_card]], colWidths=[293, 293, 293])
    t_s6_top.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_s6_top)
    story.append(Spacer(1, 10))

    csv_card = make_card(
        "📊 Transparência e Auditoria: Exportação Direta em Planilha CSV",
        "O endpoint <code>GET /admin/history</code> decodifica o arquivo binário da flash e gera em tempo real uma planilha CSV para download direto no celular do agricultor ou coordenador. "
        "Cada linha registra o carimbo de data/hora, se a água abriu, duração e o <b>código exato do motivo</b> (ex: <code>BLOCKED_COOLDOWN</code>, <code>BLOCKED_DAILY_BUDGET</code>, <code>EMERGENCY_STOP</code>). "
        "Isso permite auditar todo o histórico hídrico da comunidade sem depender de internet ou banco de dados externo.",
        styles, width=880, border_col=EMERALD, bg_col=colors.HexColor("#f0fdf4")
    )
    story.append(csv_card)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 7: MATRIZ DE SEGURANÇA E CONCLUSÃO
    # =========================================================================
    story.append(Paragraph("Matriz Consolidada de Proteções e Conclusão", styles['SlideTitle']))
    story.append(Paragraph("Síntese das proteções implementadas e impacto prático na sustentabilidade da horta", styles['SlideSubtitle']))

    tbl_matrix = [
        [Paragraph("Ameaça / Cenário de Risco", styles['TableHeader']),
         Paragraph("Mecanismo de Segurança", styles['TableHeader']),
         Paragraph("Resposta Operacional do Firmware", styles['TableHeader']),
         Paragraph("Código no Histórico", styles['TableHeader'])],

        [Paragraph("Pico de pressão hidráulica (golpe de aríete) / Cliques repetidos na interface", styles['TableCell']),
         Paragraph("<b>Cooldown Mínimo (10s)</b>", styles['TableCellBold']),
         Paragraph("Válvula travada fechada até completar repouso.", styles['TableCell']),
         Paragraph("<code>BLOCKED_COOLDOWN</code>", styles['TableCellBold'])],

        [Paragraph("Afogamento dos canteiros / Esvaziamento total da caixa d'água", styles['TableCell']),
         Paragraph("<b>Orçamento Diário (900s)</b>", styles['TableCellBold']),
         Paragraph("Bloqueia novas regas até a virada da meia-noite.", styles['TableCell']),
         Paragraph("<code>BLOCKED_DAILY_BUDGET</code>", styles['TableCellBold'])],

        [Paragraph("Erro de digitação de tempo (ex: 9999s) ou corrupção de memória", styles['TableCell']),
         Paragraph("<b>Teto Unitário (300s)</b>", styles['TableCellBold']),
         Paragraph("Poda automática de duração para no máximo 5 minutos.", styles['TableCell']),
         Paragraph("<i>Parâmetro Limitado</i>", styles['TableCell'])],

        [Paragraph("Vazamento visível ou rompimento de mangueira em campo", styles['TableCell']),
         Paragraph("<b>Parada de Emergência</b>", styles['TableCellBold']),
         Paragraph("Corte imediato de sinal no pino GPIO 2 (< 1ms).", styles['TableCell']),
         Paragraph("<code>EMERGENCY_STOP</code>", styles['TableCellBold'])],

        [Paragraph("60 acionamentos repetidos durante o mesmo minuto programado", styles['TableCell']),
         Paragraph("<b>Deduplicação de Minuto</b>", styles['TableCellBold']),
         Paragraph("Ignora requisições extras com a mesma minuteKey.", styles['TableCell']),
         Paragraph("<code>SCHEDULE</code> (1x)", styles['TableCell'])],
    ]

    t_matrix = Table(tbl_matrix, colWidths=[240, 180, 310, 150])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_GREEN),
        ('BOX', (0, 0), (-1, -1), 1, CARD_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, CARD_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, CARD_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(t_matrix)
    story.append(Spacer(1, 10))

    # Métricas de destaque
    m1 = Table([[Paragraph("4", styles['MetricValue'])], [Paragraph("Camadas de Defesa Ativa", styles['MetricLabel'])]], colWidths=[205])
    m2 = Table([[Paragraph("100%", styles['MetricValue'])], [Paragraph("Autonomia Offline (Sem Nuvem)", styles['MetricLabel'])]], colWidths=[205])
    m3 = Table([[Paragraph("900s", styles['MetricValue'])], [Paragraph("Teto Máximo Diário de Água", styles['MetricLabel'])]], colWidths=[205])
    m4 = Table([[Paragraph("&lt; 1ms", styles['MetricValue'])], [Paragraph("Corte em Emergência", styles['MetricLabel'])]], colWidths=[205])

    for m in (m1, m2, m3, m4):
        m.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, CARD_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))

    t_metrics = Table([[m1, m2, m3, m4]], colWidths=[215, 215, 215, 215])
    t_metrics.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_metrics)
    story.append(Spacer(1, 8))

    c_final = make_card(
        "🏆 Conclusão: Confiabilidade Industrial em Hardware Acessível",
        "Com boas práticas de engenharia de software (funções puras, contratos estritos, laços não-bloqueantes e filosofia fail-safe), "
        "o microcontrolador ESP32 garante a segurança integral da horta comunitária, eliminando desperdícios de água e riscos de perda da safra.",
        styles, width=880, border_col=EMERALD, bg_col=colors.HexColor("#f0fdf4")
    )
    story.append(c_final)

    # Constrói o PDF
    doc.build(story, canvasmaker=SlideCanvas, onFirstPage=draw_cover_background)
    print(f"Sucesso! Apresentação em slides atualizada (7 slides): {filename}")


if __name__ == "__main__":
    build_slides_pdf("Apresentacao_Seguranca_ESP32.pdf")
