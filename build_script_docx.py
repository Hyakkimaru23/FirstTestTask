#!/usr/bin/env python3
"""Сборка учебного Word-сценария мастер-класса."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


# Палитра
INK = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x4B, 0x55, 0x63)
GREEN = RGBColor(0x14, 0x53, 0x2D)
RED = RGBColor(0x9A, 0x24, 0x1C)
BLUE = RGBColor(0x1E, 0x40, 0xAF)
GOLD = RGBColor(0x7C, 0x4A, 0x03)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SHADE_SAY = "FDECEC"
SHADE_KIDS = "E8F0FE"
SHADE_NOTE = "F4F1E8"
SHADE_HEAD = "14532D"
SHADE_CARD = "ECFDF3"
SHADE_WARN = "FEF3C7"
SHADE_ROW = "F8FAFC"


def set_run_font(run, name="Calibri", size=12, bold=False, italic=False, color=INK):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run._element.rPr.rFonts.set(qn("w:cs"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color


def shade_paragraph(paragraph, fill):
    ppr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    ppr.append(shd)


def set_cell_shading(cell, fill):
    tc = cell._tc
    tcpr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcpr.append(shd)


def set_cell_margins(cell, **sides):
    tc = cell._tc
    tcpr = tc.get_or_add_tcPr()
    tc_mar = OxmlElement("w:tcMar")
    for side, cm_val in sides.items():
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(int(cm_val * 567)))
        node.set(qn("w:type"), "dxa")
        tc_mar.append(node)
    tcpr.append(tc_mar)


def prevent_row_split(row):
    tr = row._tr
    trpr = tr.get_or_add_trPr()
    cant = OxmlElement("w:cantSplit")
    trpr.append(cant)


def set_repeat_header(row):
    tr = row._tr
    trpr = tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    trpr.append(header)


def keep_with_next(paragraph):
    ppr = paragraph._p.get_or_add_pPr()
    kwn = OxmlElement("w:keepNext")
    ppr.append(kwn)


def keep_together(paragraph):
    ppr = paragraph._p.get_or_add_pPr()
    kl = OxmlElement("w:keepLines")
    ppr.append(kl)


def set_spacing(paragraph, before=0, after=6, line=15):
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = line / 12
    pf.widow_control = True


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)
    set_run_font(run, size=9, color=MUTED)


def add_header_footer(doc):
    section = doc.sections[0]
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.clear()
    set_spacing(hp, 0, 2, 12)
    r = hp.add_run("Фестиваль путешествий · Монголия · мастер-класс 14:30–15:00")
    set_run_font(r, size=9, color=MUTED)
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT

    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.clear()
    set_spacing(fp, 2, 0, 12)
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    left = fp.add_run("Учи наизусть карточку · сценарий — подсказка   ")
    set_run_font(left, size=9, color=MUTED)
    add_page_number(fp)


def h1(doc, text):
    p = doc.add_paragraph()
    set_spacing(p, 8, 6, 14)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(text)
    set_run_font(r, size=18, bold=True, color=GREEN)
    keep_with_next(p)
    return p


def h2(doc, text):
    p = doc.add_paragraph()
    set_spacing(p, 8, 4, 14)
    r = p.add_run(text)
    set_run_font(r, size=14, bold=True, color=GREEN)
    keep_with_next(p)
    return p


def h3(doc, text):
    p = doc.add_paragraph()
    set_spacing(p, 8, 4, 13)
    r = p.add_run(text)
    set_run_font(r, size=12, bold=True, color=GOLD)
    keep_with_next(p)
    return p


def body(doc, text, *, size=12, italic=False, color=INK, after=6, bold=False):
    p = doc.add_paragraph()
    set_spacing(p, 0, after, 15)
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold, italic=italic, color=color)
    return p


def bullet(doc, text, *, bold_lead=None):
    p = doc.add_paragraph()
    set_spacing(p, 0, 3, 14)
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.first_line_indent = Cm(-0.35)
    mark = p.add_run("• ")
    set_run_font(mark, size=12, bold=True, color=GREEN)
    if bold_lead:
        b = p.add_run(bold_lead)
        set_run_font(b, size=12, bold=True)
        r = p.add_run(text)
        set_run_font(r, size=12)
    else:
        r = p.add_run(text)
        set_run_font(r, size=12)
    return p


def say(doc, text):
    p = doc.add_paragraph()
    set_spacing(p, 2, 2, 13)
    p.paragraph_format.left_indent = Cm(0.15)
    p.paragraph_format.right_indent = Cm(0.15)
    shade_paragraph(p, SHADE_SAY)
    keep_together(p)
    tag = p.add_run("  ТЫ  ")
    set_run_font(tag, size=10, bold=True, color=WHITE)
    # tag shading via run highlight
    tag.font.highlight_color = None
    rpr = tag._element.get_or_add_rPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), "9A241C")
    rpr.append(shd)
    gap = p.add_run("  ")
    set_run_font(gap, size=12)
    spoken = p.add_run(text)
    set_run_font(spoken, size=12, bold=True, color=RED)
    return p


def kids(doc, text):
    p = doc.add_paragraph()
    set_spacing(p, 1, 2, 13)
    p.paragraph_format.left_indent = Cm(0.15)
    p.paragraph_format.right_indent = Cm(0.15)
    shade_paragraph(p, SHADE_KIDS)
    keep_together(p)
    tag = p.add_run("  ДЕТИ  ")
    set_run_font(tag, size=10, bold=True, color=WHITE)
    rpr = tag._element.get_or_add_rPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), "1E40AF")
    rpr.append(shd)
    gap = p.add_run("  ")
    set_run_font(gap, size=12)
    spoken = p.add_run(text)
    set_run_font(spoken, size=12, bold=True, color=BLUE)
    return p


def note(doc, text):
    p = doc.add_paragraph()
    set_spacing(p, 1, 3, 13)
    shade_paragraph(p, SHADE_NOTE)
    keep_together(p)
    tag = p.add_run("  ДЕЛАЙ  ")
    set_run_font(tag, size=10, bold=True, color=WHITE)
    rpr = tag._element.get_or_add_rPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), "7C4A03")
    rpr.append(shd)
    gap = p.add_run("  ")
    set_run_font(gap, size=12)
    r = p.add_run(text)
    set_run_font(r, size=11, color=GOLD)
    return p


def fill_cell(cell, text, *, bold=False, size=11, color=INK, fill=None, align="left"):
    cell.text = ""
    p = cell.paragraphs[0]
    set_spacing(p, 1, 1, 13)
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold, color=color)
    if fill:
        set_cell_shading(cell, fill)
    set_cell_margins(cell, top=0.04, bottom=0.04, left=0.1, right=0.1)


def add_table(doc, headers, rows, col_widths, *, font=11):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for i, w in enumerate(col_widths):
        for cell in table.columns[i].cells:
            cell.width = Cm(w)
    for i, h in enumerate(headers):
        fill_cell(table.rows[0].cells[i], h, bold=True, size=10, color=WHITE, fill=SHADE_HEAD, align="center")
    set_repeat_header(table.rows[0])
    prevent_row_split(table.rows[0])
    for r_i, row in enumerate(rows):
        fill = SHADE_ROW if r_i % 2 == 0 else "FFFFFF"
        for c_i, val in enumerate(row):
            fill_cell(table.rows[r_i + 1].cells[c_i], val, size=font, fill=fill)
        prevent_row_split(table.rows[r_i + 1])
    spacer = doc.add_paragraph()
    set_spacing(spacer, 0, 2, 10)
    return table


def build(path: Path):
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)
    section.top_margin = Cm(1.6)
    section.bottom_margin = Cm(1.5)
    section.header_distance = Cm(0.6)
    section.footer_distance = Cm(0.5)
    add_header_footer(doc)

    # Титул
    t = doc.add_paragraph()
    set_spacing(t, 0, 2, 14)
    r = t.add_run("СЦЕНАРИЙ НА 30 МИНУТ")
    set_run_font(r, size=11, bold=True, color=GOLD)

    t2 = doc.add_paragraph()
    set_spacing(t2, 0, 2, 16)
    r = t2.add_run("Мастер-класс «Учимся стрельбе из лука»")
    set_run_font(r, size=22, bold=True, color=GREEN)

    t3 = doc.add_paragraph()
    set_spacing(t3, 0, 8, 14)
    r = t3.add_run("Фестиваль путешествий · Монголия · ~30 детей · 1 лук · ты в дээле")
    set_run_font(r, size=12, color=MUTED)

    body(
        doc,
        "Как учить: наизусть раздел 1. Один раз вслух — раздел 3. На площадке красные блоки можно читать с листа.",
        italic=True,
        color=MUTED,
        after=4,
    )
    add_table(
        doc,
        ["Цвет", "Кто", "Что это"],
        [
            ["Красный «ТЫ»", "Твои слова", "Говори вслух. Можно читать."],
            ["Синий «ДЕТИ»", "Ответ зала", "Жди хор, не монолог."],
            ["Бежевый «ДЕЛАЙ»", "Твоё тело", "Не произноси залу."],
        ],
        [4.4, 4.4, 9.2],
    )

    # ===== КАРТОЧКА =====
    h1(doc, "1. Карточка. Выучи это")

    h2(doc, "Хронометраж")
    add_table(
        doc,
        ["Время", "Блок", "Если опаздываешь"],
        [
            ["0:00–1:30", "Вход + 2 пароля", "Пароли обязательны. Без них зал не собрать."],
            ["1:30–4:00", "3 закона степи", "Не читай лекцию. Спроси хором и иди дальше."],
            ["4:00–9:00", "Воздушный лук всем + 3 тумэна", "3 волны. Тумэны рукой, не по списку."],
            ["9:00–24:00", "Конвейер: 1 выстрел на ребёнка", "Цель: 20 секунд на человека."],
            ["24:00–27:30", "Охота: 3 героя", "РЕЗАТЬ ПЕРВОЙ, если не все стрельнули."],
            ["27:30–30:00", "Клятва → сдать на юрту", "Не отпускай толпу в никуда."],
        ],
        [3.2, 7.0, 7.8],
    )
    body(
        doc,
        "Часы на запястье. Таймер 28 минут. В 14:52 нет очереди? Режь охоту. В 14:54 ещё стреляют? "
        "Оставшимся — выстрел «с баатаром» (твои руки поверх их), по 10 секунд.",
        bold=True,
        after=8,
    )

    h2(doc, "Железное правило")
    body(
        doc,
        "Не строй очередь к луку. Пока один стреляет, остальные — хор: ветер «у-у-у» и крик «УУХАЙ!». "
        "Рот не закрывай. Пауза = хаос.",
    )

    h2(doc, "Два пароля — кнопка тишины")
    add_table(
        doc,
        ["Ты", "Дети"],
        [
            ["ВОИНЫ СТЕПИ!", "ЗДЕСЬ! + рука вверх"],
            ["ВЕТЕР!", "Замирают столбом"],
        ],
        [8.0, 10.0],
    )

    h2(doc, "Три закона")
    bullet(doc, "Лук смотрит только в степь (мишень). Не в людей, не в пол, не в небо.", bold_lead="1. ")
    bullet(doc, "Тетиву трогает только тот, кому ты дал лук. У остальных — воздушный лук.", bold_lead="2. ")
    bullet(doc, "Стрела летит только после твоего «ГАЛ!». Это твоя команда, не монгольское слово.", bold_lead="3. ")

    h2(doc, "Формула одного выстрела (говори одно и то же)")
    say(doc, "Воин, на линию! Как зовут?")
    note(doc, "Сам вставляешь стрелу. Ребёнок только натягивает и отпускает. Следующий уже стоит сзади в стойке.")
    say(doc, "Боком. Ноги как на коне. Рука до щеки. Степь тебя видит… ГАЛ!")
    body(doc, "Попал:", bold=True, after=2)
    say(doc, "УУХАЙ! [Имя], баатар!")
    kids(doc, "УУХАЙ!")
    body(doc, "Мимо — никогда не говори «промах» / «не получилось»:", bold=True, after=2)
    say(doc, "Ветер унёс! Рука не дрогнула. Уухай за смелость! [Имя] уже лучник.")
    say(doc, "Лук баатару. Следующий!")

    h2(doc, "Восемь фраз от тупняка")
    body(doc, "Мозг пустой — говори любую и делай жест. Не стой молча.", italic=True, color=MUTED, after=4)
    add_table(
        doc,
        ["№", "Говори"],
        [
            ["1", "ВОИНЫ СТЕПИ!"],
            ["2", "Покажите стойку на коне. Ещё гордее."],
            ["3", "Ветер, кто громче уухай — тому степь помогает."],
            ["4", "Смотрите на руки [имя]. Вот это тетива."],
            ["5", "Стрела летит туда, куда смотрит палец, не нос."],
            ["6", "Кто без лука — вы не ждёте. Вы натягиваете небо."],
            ["7", "Громкий отряд стреляет точнее. Проверим."],
            ["8", "Следующий уже на линии. Степь не любит паузы."],
        ],
        [1.4, 16.6],
    )

    h2(doc, "Клятва в конце (по кускам, они повторяют)")
    say(doc, "Я берегу лук.")
    say(doc, "Я не целюсь в людей.")
    say(doc, "Я стреляю только в степь.")
    say(doc, "Я путешественник и баатар.")

    # ===== ПОДГОТОВКА =====
    h1(doc, "2. До детей. 15 минут")

    h2(doc, "Площадка")
    bullet(doc, "Мишень большая, 2–3 метра. Для присосок — гладкая вертикаль. Чем легче попасть, тем громче зал.")
    bullet(doc, "Линия огня — скотч. Ты стоишь на линии и почти не уходишь.")
    bullet(doc, "Дети слева цепочкой. Никто не ходит за мишень и поперёк выстрела.")
    bullet(doc, "Стрелы только у тебя за поясом. Пачкой детям не давать.")
    bullet(doc, "Попроси одного взрослого в хвост очереди. Нет взрослого — линия короткая и плотная, справишься.")

    h2(doc, "С собой")
    add_table(
        doc,
        ["Взять", "Зачем"],
        [
            ["Лук + все присоски (лучше 3)", "Не бегать за одной стрелой каждый раз"],
            ["Скотч + запасная резинка", "Линия и живая тетива"],
            ["Большая мишень + запасной лист", "Если порвут"],
            ["Вода, часы на запястье", "Говорить 30 минут; телефон в кармане не смотри"],
            ["3 ленты / стикера цветов", "Солнце / Конь / Ветер на запястье за 20 сек"],
        ],
        [7.2, 10.8],
    )

    h2(doc, "Сдача с прошлого блока")
    body(
        doc,
        "Договорись с ведущим 14:00. Ты уже в костюме на линии. Он сдаёт группу фразой:",
        after=3,
    )
    say(doc, "Путешественники, в Монголии без лука не становятся воинами. Вас ждёт баатар!")
    p_end = body(doc, "Не сиди в уголке. Не извиняйся, что первый раз. Дети видят уверенность, не стаж.")
    keep_with_next(p_end)

    # ===== СЦЕНАРИЙ =====
    doc.add_page_break()
    h1(doc, "3. Сценарий слово в слово")
    body(
        doc,
        "Этот раздел не зубрить. Один раз проговори вслух. На площадке читай красные строки, если выпал.",
        italic=True,
        color=MUTED,
        after=6,
    )

    h2(doc, "0:00–1:30 · Вход")
    note(doc, "Встань, чтобы видели все. Лук в руке.")
    say(doc, "Стой! Кто идёт по земле великой Монголии?")
    note(doc, "Пауза 1 секунда.")
    say(doc, "Я вижу путешественников. Страну на карте вы уже нашли. Флажок поставили. В Монголии гостя принимают в юрте. Воина — только после выстрела!")
    say(doc, "Я баатар. По-монгольски «баатар» — герой. Повторите: БАА-ТАР!")
    kids(doc, "Баатар!")
    say(doc, "Сайн байна уу! Так говорят «здравствуйте». Скажите: сайн байна уу!")
    kids(doc, "Сайн байна уу!")
    note(doc, "Поклонись.")
    say(doc, "Пароль отряда. Я кричу «ВОИНЫ СТЕПИ!» — вы «ЗДЕСЬ!» и рука вверх. ВОИНЫ СТЕПИ!")
    kids(doc, "ЗДЕСЬ!")
    note(doc, "Повтори второй раз — уже чётко.")
    say(doc, "Второй пароль. «ВЕТЕР!» — все замирают. Ветер слушает тех, кто не шевелится. ВЕТЕР!")
    note(doc, "Похвали самых неподвижных по имени, если слышишь.")
    say(doc, "Вот это воины. Степь вас приняла.")

    h2(doc, "1:30–4:00 · Три закона")
    say(doc, "Лук — не игрушка. Три закона. Кто нарушит — стреляет последним. Кто запомнит — в первом тумэне.")
    say(doc, "Закон один. Лук смотрит только в степь. Степь — это мишень. Куда смотрит лук?")
    kids(doc, "В степь!")
    say(doc, "Закон два. Тетиву трогает только тот, кому я дал лук. Остальные держат воздушный лук. Покажите!")
    note(doc, "Все изображают лук — уже заняты.")
    say(doc, "Закон три. Стрела летит только по слову баатара. Слово: ГАЛ! Кто выстрелил без «гал» — ход пропускает.")
    say(doc, "Какой первый закон?")
    note(doc, "Трое, кто орёт громче, потом стреляют первыми.")

    h2(doc, "4:00–9:00 · Воздушный лук + тумэны")
    body(
        doc,
        "Это спасает вечер: 30 человек заняты, лук ещё лежит. Не пропускай блок ради «скорее стрелять» — "
        "иначе очередь сомнётся.",
        italic=True,
        color=MUTED,
    )
    say(doc, "Настоящий лучник сначала учится телом. Встаньте боком к мишени, как я!")
    note(doc, "Показывай крупно, медленно, один раз.")
    say(doc, "Ноги — как на коне. Левая смотрит в степь, правая держит седло.")
    say(doc, "Левая рука держит лук. Правая тянет тетиву до щеки. Не до уха — до щеки. Шепчешь стреле секрет.")
    say(doc, "Спина прямая. Выдох — и отпускаем. Не дёргаем.")

    h3(doc, "Волна 1. Тихий ветер")
    say(doc, "Натянуть… держать… ВЕТЕР! … ГАЛ!")
    note(doc, "10 секунд ходи: хвали стойку по именам.")

    h3(doc, "Волна 2. Скачка")
    say(doc, "Монголы стреляли с коня! На месте — галоп ногами, лук натянуть, ГАЛ!")

    h3(doc, "Волна 3. Уухай")
    say(doc, "Когда лучник попадает, все кричат УУХАЙ! Это крик праздника Наадам: борьба, скачки, лук. Сейчас выстрел — и уухай.")
    kids(doc, "УУХАЙ!")

    h3(doc, "Деление")
    note(doc, "Пока орёт третья волна — рукой режь на 3 кучи по ~10. Не по списку.")
    say(doc, "Вы десять — тумэн Солнца, сюда. Вы — Конь. Вы — Ветер.")
    say(doc, "Первым стреляет тот тумэн, который лучше замер на «ВЕТЕР!». Проверка. ВЕТЕР!")
    note(doc, "Ленту/стикер на запястье — если взял. Если нет, просто кучками у линии.")

    h2(doc, "9:00–24:00 · Конвейер")
    body(doc, "Цель: все по одному выстрелу. 30 × 20 сек ≈ 10 минут. Запас на малышей и заминки.", after=4)

    h3(doc, "Техника (не объявляй залу, просто делай)")
    bullet(doc, "Стрелу вставляешь ты.")
    bullet(doc, "Следующий уже за спиной стрелка, воздушный лук натянут.")
    bullet(doc, "После выстрела лук сразу тебе. «Ещё разочек» — только в хвосте, если время есть.")
    bullet(doc, "Стрелу снимаешь ты после «Стрелу домой!». Один дежурный ребёнок — только если взрослый рядом.")
    bullet(doc, "Не смотри в зал в тишине. Либо формула выстрела, либо фраза из карточки, либо факт.")

    h3(doc, "Что делают остальные")
    body(
        doc,
        "Не крути три роли по кругу — запутаешься. Одно занятие на всех, кто не стреляет:",
        after=4,
    )
    add_table(
        doc,
        ["Когда", "Зал делает"],
        [
            ["Стрела летит", "Ветер: у-у-у"],
            ["Попал или смелый промах", "УУХАЙ!"],
            ["Ты чинишь лук / вставляешь стрелу", "Стойка на коне + воздушный лук"],
        ],
        [6.5, 11.5],
    )
    body(
        doc,
        "Тумэны нужны, чтобы звать к линии пачками («Солнце, на линию!»), не чтобы вести три игры сразу.",
        italic=True,
        color=MUTED,
    )

    h3(doc, "Вставки, пока вставляешь стрелу (крути по кругу)")
    bullet(doc, "Монголы стреляли вперёд и назад на полном скаку.")
    bullet(doc, "Лук клеили из дерева, рога и сухожилий. Короткий — чтобы с коня.")
    bullet(doc, "Наадам — праздник трёх игр: борьба, кони, лук. Вы в третьей.")
    bullet(doc, "Кто сегодня в дээле — в том же плаще, в каком ездили по степи.")
    bullet(doc, "Сейчас полетит стрела. Тишина…")

    h3(doc, "Малыш / боится / «лук не для девочек»")
    bullet(doc, "Встань сзади, руки поверх, вместе «гал». Скажи: «Выстрел с баатаром».", bold_lead="5 лет: ")
    bullet(doc, "Не заставляй. «Ты сегодня ветер отряда. Без ветра стрела не летит». Дай командовать уухай. Часто через 2 минуты сами просят лук.", bold_lead="Боится: ")
    bullet(doc, "«В степи воином может быть каждый. Кто следующий баатар?»", bold_lead="Спор: ")

    h2(doc, "24:00–27:30 · Охота трёх (режется)")
    body(doc, "Только если все уже стрельнули. Иначе сразу клятва.", bold=True, after=4)
    say(doc, "Слушайте степь! По каравану идёт тень волка. Один тумэн — один выстрел за всех. Кого пошлёте?")
    note(doc, "5 секунд на выбор. Или сам тыкни того, кто грустил / не стрелял.")
    say(doc, "Солнце — ваш звук «Ай!». Конь — цокот языком. Ветер — у-у-у. Герой на линию.")
    note(doc, "Три выстрела. Ближе к центру — титул «Ханский стрелок фестиваля». Все три тумэна всё равно приняты в отряд.")

    h2(doc, "27:30–30:00 · Клятва и сдача")
    note(doc, "Лук вверх.")
    say(doc, "Воины степи! Вы пришли путешественниками. Уходите лучниками Монголии. Повторяйте клятву по строке.")
    say(doc, "Я берегу лук. / Я не целюсь в людей. / Я стреляю только в степь. / Я путешественник и баатар.")
    kids(doc, "(хором повторяют каждую строку)")
    say(doc, "Сайн байна уу мы уже говорили. Теперь баярлалаа — спасибо. Скажите степи: БАЯРЛАЛАА!")
    kids(doc, "Баярлалаа!")
    say(doc, "Дальше — юрта и конь-оберег. Когда будете клеить наклейку на чемодан, вы уже не гости. Вы держали монгольский лук. ВОИНЫ СТЕПИ!")
    kids(doc, "ЗДЕСЬ!")
    note(doc, "Сдай группу следующему ведущему за руку. Не «ну ладно, идите туда».")

    # ===== СБОИ =====
    h1(doc, "4. Если сломалось")
    add_table(
        doc,
        ["Ситуация", "Делай", "Говори"],
        [
            [
                "Лук заело / тетива",
                "Не чини молча. 20 сек. Не чинится — до конца бумажные «стрелы» в коробку + клятва.",
                "Степь проверяет нас. Пока лук пьёт ветер — три стойки. Самый красивый воин подходит первым.",
            ],
            [
                "Толкаются / ор",
                "«ВЕТЕР!». Двоих в «совет хана» считать попадания. Нотацию не читай.",
                "В степи ссорятся словами, не локтями. Лук — после отряда.",
            ],
            [
                "Никто не первый",
                "Сам красиво попади.",
                "Тогда стреляет баатар. Степь открыта. Кто повторит?",
            ],
            [
                "Все хотят ещё",
                "Второй круг — только хвост времени, кому не досталось.",
                "Настоящий лучник делает один честный выстрел.",
            ],
            [
                "Шум, тебя не слышно",
                "Не ори поверх. Шёпот + рука вверх.",
                "Кто услышал шёпот степи — тот уже воин.",
            ],
            [
                "Родители снимают",
                "Используй.",
                "Воины, нас видит весь караван. Стойка!",
            ],
            [
                "Очередь встала",
                "Пароль. Следующий уже на линии.",
                "ВОИНЫ СТЕПИ! Следующий на линию.",
            ],
        ],
        [3.6, 7.2, 7.2],
        font=10,
    )

    # ===== РЕПЕТИЦИЯ =====
    h1(doc, "5. Репетиция сегодня. 12 минут")
    body(doc, "Вслух. Хоть перед шкафом. Костюм — если уже есть.", after=4)
    add_table(
        doc,
        ["Мин", "Что проговорить"],
        [
            ["2", "Приветствие + два пароля"],
            ["2", "Три закона"],
            ["3", "Показ стойки + три волны"],
            ["3", "Формула выстрела 4 раза подряд: имя — конь — гал — уухай — следующий"],
            ["2", "Клятва"],
        ],
        [2.2, 15.8],
    )
    h1(doc, "6. Порядок под огнём")
    p = doc.add_paragraph()
    set_spacing(p, 4, 8, 16)
    shade_paragraph(p, SHADE_CARD)
    r = p.add_run(
        "Пароли → 3 закона → воздушный лук → 3 тумэна → "
        "конвейер (ты вставляешь стрелу) → уухай → "
        "охота только если все стрельнули → клятва → юрта"
    )
    set_run_font(r, size=13, bold=True, color=GREEN)

    body(
        doc,
        "Если формула выстрела крутится без запинки — на площадке ты уже не новичок.",
        bold=True,
        after=6,
    )

    body(
        doc,
        "Слова: баатар — герой. сайн байна уу — здравствуйте. баярлалаа — спасибо. уухай — крик попадания на Наадаме. "
        "тумэн — отряд. дээл — халат на тебе. гал — твоя команда «огонь».",
        italic=True,
        color=MUTED,
        after=2,
    )

    out = Path(path)
    doc.save(out)
    return out


if __name__ == "__main__":
    target = Path("/workspace/Master-klass_luk_Mongolia.docx")
    build(target)
    print(target, target.stat().st_size)
