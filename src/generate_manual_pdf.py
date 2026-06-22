import os
import sys
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether

# Paths to the generated screen mockup images
IMAGE_MAIN = "interface.png"
PDF_PATH = "Manual_TopoCalc.pdf"

# Document layout variables
PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 20 * mm
RIGHT_MARGIN = 20 * mm
TOP_MARGIN = 22 * mm
BOTTOM_MARGIN = 22 * mm
PRINTABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

def build_pdf():
    # Setup document
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN
    )

    # Styles
    styles = getSampleStyleSheet()
    
    # Custom colors
    slate_blue = colors.HexColor("#1a2b4c")
    teal_accent = colors.HexColor("#0d9488")
    dark_gray = colors.HexColor("#1f2937")
    light_bg = colors.HexColor("#f3f4f6")
    
    # Custom styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=30,
        textColor=slate_blue,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=13,
        leading=16,
        textColor=teal_accent,
        alignment=TA_CENTER
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=slate_blue,
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=teal_accent,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=dark_gray,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=dark_gray,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )

    list_style = ParagraphStyle(
        'List_Custom',
        parent=body_style,
        leftIndent=15,
        spaceAfter=4
    )
    
    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
        backColor=light_bg,
        borderColor=colors.HexColor("#e2e8f0"),
        borderWidth=0.5,
        borderPadding=8,
        spaceBefore=6,
        spaceAfter=8
    )
    
    caption_style = ParagraphStyle(
        'Caption',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#4b5563"),
        alignment=TA_CENTER,
        spaceAfter=12
    )

    meta_label_style = ParagraphStyle(
        'MetaLabel',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=slate_blue
    )
    
    meta_val_style = ParagraphStyle(
        'MetaValue',
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=dark_gray
    )

    story = []

    # ------------------ COVER PAGE ------------------
    story.append(Spacer(1, 40 * mm))
    story.append(Paragraph("TOPOCALC", title_style))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Manual Técnico do Usuário & Documentação", subtitle_style))
    story.append(Spacer(1, 15 * mm))
    
    # Colored horizontal separator
    sep_table = Table([[""]], colWidths=[PRINTABLE_WIDTH], rowHeights=[2])
    sep_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), teal_accent)]))
    story.append(sep_table)
    story.append(Spacer(1, 15 * mm))
    
    # Metadata Block
    meta_data = [
        [Paragraph("Release:", meta_label_style), Paragraph("Alpha v0.2.0", meta_val_style)],
        [Paragraph("Data:", meta_label_style), Paragraph("21 de junho de 2026", meta_val_style)],
        [Paragraph("Autor:", meta_label_style), Paragraph("Pablo Medina Camacho", meta_val_style)],
        [Paragraph("Email:", meta_label_style), Paragraph("pablo@pablomc.com", meta_val_style)],
        [Paragraph("Curso:", meta_label_style), Paragraph("Engenharia Civil Empresarial", meta_val_style)],
        [Paragraph("Instituição:", meta_label_style), Paragraph("Universidade Federal do Rio Grande (FURG)", meta_val_style)],
        [Paragraph("Linguagem:", meta_label_style), Paragraph("Python (PySide6 + bibliotecas científicas)", meta_val_style)],
        [Paragraph("Licença:", meta_label_style), Paragraph("Uso acadêmico e não comercial (similar à CC BY-NC 4.0)", meta_val_style)],
    ]
    
    meta_table = Table(meta_data, colWidths=[35 * mm, PRINTABLE_WIDTH - 35 * mm])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    
    story.append(meta_table)
    story.append(Spacer(1, 20 * mm))
    
    # Brief description card
    desc_p = Paragraph(
        "<b>Objetivo:</b> Sistema desenvolvido para cálculos de fechamento topográficos, exclusivo para poligonais fechadas.",
        ParagraphStyle('Desc', parent=body_style, fontSize=10, leading=14, textColor=slate_blue)
    )
    desc_table = Table([[desc_p]], colWidths=[PRINTABLE_WIDTH])
    desc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('BOX', (0,0), (-1,-1), 1, teal_accent),
        ('PADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(desc_table)
    
    story.append(PageBreak())

    # ------------------ SECTION 1: SOBRE O SISTEMA ------------------
    story.append(Paragraph("1. SOBRE O SISTEMA", h1_style))
    story.append(Paragraph(
        "O TopoCalc é um software computacional especializado voltado ao cálculo e compensação "
        "de poligonais topográficas fechadas. Desenvolvido no contexto acadêmico do curso de "
        "Engenharia Civil Empresarial da Universidade Federal do Rio Grande (FURG), o sistema "
        "integra algoritmos clássicos de topografia com uma interface gráfica rica, intuitiva e "
        "responsiva escrita em Python e PySide6.",
        body_style
    ))
    story.append(Paragraph(
        "O principal objetivo do programa é otimizar as etapas de escritório, eliminando "
        "planilhas manuais e garantindo a consistência geométrica dos levantamentos por meio de "
        "um sistema de validação em tempo real e de compensação pelo método proporcional de Bowditch.",
        body_style
    ))
    
    # ------------------ SECTION 2: ENTRADA DE DADOS ------------------
    story.append(Paragraph("2. ENTRADA DE DADOS E FORMATAÇÃO", h1_style))
    story.append(Paragraph(
        "Para realizar cálculos precisos, o TopoCalc exige uma entrada de dados estruturada. "
        "As seguintes diretrizes devem ser seguidas ao alimentar a caderneta de campo do software:",
        body_style
    ))
    story.append(Paragraph(
        "<b>• Inserção de Vértices:</b> Cada ponto topográfico (estação ou vértice) deve ser inserido "
        "individualmente informando seu nome identificador (ex: V1, V2, P1), o ângulo horizontal "
        "interno observado e a distância horizontal correspondente ao alinhamento atual.",
        list_style
    ))
    story.append(Paragraph(
        "<b>• Formato de Coordenadas:</b> O sistema opera em coordenadas planas cartesianas lineares "
        "(eixo Leste/X e eixo Norte/Y). A coordenada de partida da primeira estação é considerada "
        "arbitrariamente como (0.0, 0.0) para fins de cálculo de propagação planimétrica relativa.",
        list_style
    ))
    story.append(Paragraph(
        "<b>• Ângulos em DMS:</b> A inserção de ângulos lidos é realizada informando Graus, Minutos e "
        "Segundos separadamente. Restrições do sistema impedem a digitação de valores fora do "
        "intervalo sexagesimal padrão (0 a 59 para minutos e segundos).",
        list_style
    ))

    # ------------------ SECTION 3: CÁLCULOS DISPONÍVEIS ------------------
    story.append(Paragraph("3. CÁLCULOS E METODOLOGIAS CIENTÍFICAS", h1_style))
    story.append(Paragraph(
        "O processamento matemático do TopoCalc é executado instantaneamente ao clicar em calcular, "
        "gerando os seguintes elementos:",
        body_style
    ))
    story.append(Paragraph(
        "<b>• Azimutes e Rumos:</b> A propagação de azimutes inicia-se a partir da orientação informada "
        "(azimute de partida entre V1 e V2) e é transmitida vértice a vértice somando ou subtraindo os "
        "ângulos internos compensados. O rumo é obtido pela conversão direta dos azimutes em quadrantes "
        "(NE, SE, SW, NW).",
        list_style
    ))
    story.append(Paragraph(
        "<b>• Projeções Planas Parciais:</b> Decomposição trigonométrica dos lados medidos em parciais "
        "lineares através de Delta X (Leste/Oeste) = Distância * sen(Azimute) e Delta Y (Norte/Sul) = "
        "Distância * cos(Azimute).",
        list_style
    ))
    story.append(Paragraph(
        "<b>• Erro e Ajuste de Bowditch:</b> Os erros de fechamento lineares cumulativos (Dx e Dy) "
        "permitem o cálculo do erro linear total. O ajuste é feito distribuindo esse erro de fechamento "
        "linear proporcionalmente às distâncias dos lados medidos, corrigindo as parciais e "
        "gerando coordenadas retangulares compensadas finais.",
        list_style
    ))
    story.append(Paragraph(
        "<b>• Área de Gauss e Perímetro:</b> A área total plana do polígono é obtida aplicando a fórmula "
        "de Gauss (duplas áreas) a partir das coordenadas compensadas dos vértices. O perímetro representa "
        "o somatório total das distâncias dos alinhamentos.",
        list_style
    ))

    # ------------------ INSERT IMAGE 1 ------------------
    if os.path.exists(IMAGE_MAIN):
        # A4 margins: page is 210mm wide. Left/Right margin: 20mm each. Printable width: 170mm (~480 points)
        # Scaled image width to 160mm (~450 pt), maintaining aspect ratio
        story.append(Spacer(1, 4 * mm))
        story.append(Image(IMAGE_MAIN, width=160 * mm, height=100 * mm))
        story.append(Paragraph("Figura 1: Tela Principal do TopoCalc com Área de Desenho (Croqui) e Barra de Ferramentas.", caption_style))
        story.append(Spacer(1, 4 * mm))

    story.append(PageBreak())

    # ------------------ SECTION 4: IMPORTAÇÕES E EXPORTAÇÕES ------------------
    story.append(Paragraph("4. IMPORTAÇÃO E EXPORTAÇÃO DE ARQUIVOS", h1_style))
    story.append(Paragraph(
        "O TopoCalc possui ampla interoperabilidade com softwares de SIG (QGIS, ArcGIS) e CAD (AutoCAD), "
        "além de exportar planilhas para Excel e relatórios técnicos em PDF.",
        body_style
    ))
    
    story.append(Paragraph("Mapeamento do Importador CSV:", h2_style))
    story.append(Paragraph(
        "O leitor de arquivos do TopoCalc é tolerante a acentuações, espaços e variações de letras "
        "(case-insensitive). Abaixo estão os sinônimos de colunas mapeados no sistema:",
        body_style
    ))

    # Column mappings table
    table_headers = [
        Paragraph("<b>Dado</b>", meta_label_style),
        Paragraph("<b>Cabeçalhos Aceitos no CSV</b>", meta_label_style),
        Paragraph("<b>Exemplo de Dado</b>", meta_label_style)
    ]
    
    csv_rows = [
        table_headers,
        [Paragraph("Ponto/Vértice", meta_val_style), Paragraph("ponto, point, nome do ponto, vertex, vertice, estacao, estação, est, station", meta_val_style), Paragraph("V1, Est01", meta_val_style)],
        [Paragraph("Graus", meta_val_style), Paragraph("graus, g, grau, angulo grau, deg, degrees", meta_val_style), Paragraph("105, 90", meta_val_style)],
        [Paragraph("Minutos", meta_val_style), Paragraph("minutos, m, min, angulo minuto, minutes", meta_val_style), Paragraph("30, 0", meta_val_style)],
        [Paragraph("Segundos", meta_val_style), Paragraph("segundos, s, sec, angulo segundo, seconds", meta_val_style), Paragraph("45.12, 0.0", meta_val_style)],
        [Paragraph("Distância (m)", meta_val_style), Paragraph("distancia, distance, distância, comprimento, dist, len, length", meta_val_style), Paragraph("150.25, 80,14", meta_val_style)],
        [Paragraph("Observação", meta_val_style), Paragraph("observacao, observação, notes, nota, comentario, obs, observacoes", meta_val_style), Paragraph("Divisa, Muro", meta_val_style)],
    ]
    
    csv_table = Table(csv_rows, colWidths=[25 * mm, PRINTABLE_WIDTH - 60 * mm, 35 * mm])
    csv_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0,0), (-1,0), light_bg),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    
    story.append(csv_table)
    story.append(Spacer(1, 8 * mm))

    # AI Prompt description
    story.append(Paragraph("Conversão de Dados Grandes ou Desorganizados por IA:", h2_style))
    story.append(Paragraph(
        "Se os dados estiverem em cadernetas de campo extensas, notas de texto brutas ou formatos de estação total, "
        "você pode copiar o prompt abaixo e utilizá-lo em uma IA (como ChatGPT ou Gemini) para gerar o CSV pronto:",
        body_style
    ))
    
    prompt_text = (
        "Você é um assistente especialista em topografia. Preciso que converta os dados brutos de campo fornecidos a seguir em um formato CSV limpo estruturado para o software TopoCalc.\n\n"
        "Instruções:\n"
        "1. O delimitador deve ser ponto e vírgula (;).\n"
        "2. Cabeçalho exato: Ponto;Graus;Minutos;Segundos;Distancia;Observacao\n"
        "3. Identifique os ângulos e separe-os em Graus, Minutos e Segundos.\n"
        "4. Use o ponto (.) como separador decimal para distância e segundos.\n"
        "5. Retorne APENAS o código do arquivo CSV, sem explicações adicionais ou marcações.\n\n"
        "Dados para converter:\n"
        "[Cole seus dados brutos de campo aqui]"
    )
    story.append(Paragraph(prompt_text.replace("\n", "<br/>"), code_style))

    # ------------------ SECTION 5: VALIDAÇÃO E INTERFACE ------------------
    story.append(Paragraph("5. VALIDAÇÃO GEOMÉTRICA E INTERFACE", h1_style))
    story.append(Paragraph(
        "O TopoCalc implementa um sistema de validação em tempo real que atua na aba 'Validação'. "
        "O objetivo é evitar o processamento de dados inconsistentes de campo:",
        body_style
    ))
    story.append(Paragraph(
        "<b>• Tipos de Avisos:</b> Alertas sobre dados ausentes opcionais, como descrição de projeto vazia, "
        "localidade ou contratante não preenchidos.",
        list_style
    ))
    story.append(Paragraph(
        "<b>• Tipos de Erros Críticos:</b> Erros que impedem a execução dos cálculos ou a exportação, "
        "tais como ângulos DMS inválidos (minutos/segundos maiores que 59), distâncias negativas, "
        "menos de 3 vértices no projeto ou nomes de vértices duplicados.",
        list_style
    ))
    story.append(Paragraph(
        "<b>• Rastreabilidade do Erro:</b> Ao clicar duas vezes ou dar um clique simples em qualquer mensagem "
        "de erro na lista da aba Validação, o software foca e seleciona a respectiva célula na caderneta de campo "
        "e destaca o vértice na prancha gráfica do croqui, facilitando correções rápidas.",
        list_style
    ))



    # ------------------ FOOTER & HEADER SETUP ------------------
    def add_page_decorations(canvas, doc_obj):
        canvas.saveState()
        
        # Only draw headers and footers on pages after the first page (cover)
        if doc_obj.page > 1:
            # Header
            canvas.setFont("Helvetica-Bold", 8)
            canvas.setFillColor(slate_blue)
            canvas.drawString(LEFT_MARGIN, PAGE_HEIGHT - 12 * mm, "TopoCalc - Manual do Usuário")
            
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor("#4b5563"))
            canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 12 * mm, "Identidade & Documentação Técnica")
            
            # Header line
            canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
            canvas.setLineWidth(0.5)
            canvas.line(LEFT_MARGIN, PAGE_HEIGHT - 14 * mm, PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 14 * mm)
            
            # Footer
            canvas.line(LEFT_MARGIN, BOTTOM_MARGIN - 4 * mm, PAGE_WIDTH - RIGHT_MARGIN, BOTTOM_MARGIN - 4 * mm)
            
            footer_text = f"v0.2.0 | Release: 21 de Junho de 2026 | Autor: Pablo Medina Camacho"
            canvas.drawString(LEFT_MARGIN, BOTTOM_MARGIN - 10 * mm, footer_text)
            
            page_str = f"Página {doc_obj.page}"
            canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, BOTTOM_MARGIN - 10 * mm, page_str)
            
        canvas.restoreState()

    # Build the document
    doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=add_page_decorations)
    print("PDF successfully generated.")

if __name__ == "__main__":
    build_pdf()
