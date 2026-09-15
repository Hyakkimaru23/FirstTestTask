#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tumen Tur logo brief. Baikal now; Altai and Mongolia later. Site contour is the mark."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Flowable, Image, KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("Inter", "/usr/share/fonts/truetype/macos/Inter-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Semi", "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Bold", "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"))
pdfmetrics.registerFont(TTFont("NotoSerif-Bold", "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"))

NAVY = HexColor("#0B2A4A")
TEAL = HexColor("#1A5F7A")
INK = HexColor("#1C2430")
MUTED = HexColor("#5B6573")
LINE = HexColor("#D5D0C6")
PAPER = HexColor("#FBF8F3")
CARD = HexColor("#F3EEE4")
ACCENT = HexColor("#C45C26")
OK = HexColor("#1F6B45")
NO = HexColor("#A33B24")
W, H = A4
OUT = "/workspace/docs/tumen-tur-logotip.pdf"
LOGO = "/workspace/brand/tumen-tur/source/logo-saita.png"
KONTUR = "/workspace/brand/tumen-tur/source/kontur-s-saita-chernyj.png"


class Callout(Flowable):
    def __init__(self, title, body, kind="do"):
        super().__init__()
        self.title = title
        self.body = body
        pal = {
            "do": (HexColor("#E7F1EA"), OK),
            "dont": (HexColor("#F8E8E4"), NO),
            "fact": (HexColor("#E8EEF3"), TEAL),
            "warn": (HexColor("#F8EDE4"), ACCENT),
        }
        self.bg, self.accent = pal[kind]

    def wrap(self, aw, ah):
        self.width = aw
        st = S()
        t = Paragraph(f"<b>{self.title}</b>", st["boxTitle"])
        b = Paragraph(self.body, st["boxBody"])
        _, th = t.wrap(aw - 18, 80)
        _, bh = b.wrap(aw - 18, 500)
        self._t, self._th, self._b, self._bh = t, th, b, bh
        self.height = 8 + th + 4 + bh + 8
        return aw, self.height

    def draw(self):
        self.canv.setFillColor(self.bg)
        self.canv.roundRect(0, 0, self.width, self.height, 5, fill=1, stroke=0)
        self.canv.setFillColor(self.accent)
        self.canv.rect(0, 0, 3.5, self.height, fill=1, stroke=0)
        self._t.drawOn(self.canv, 10, self.height - 6 - self._th)
        self._b.drawOn(self.canv, 10, 8)


def S():
    return {
        "h1": ParagraphStyle("h1", fontName="NotoSerif-Bold", fontSize=16, leading=20, textColor=NAVY, spaceAfter=7),
        "h2": ParagraphStyle("h2", fontName="Inter-Bold", fontSize=11.2, leading=14.5, textColor=NAVY, spaceBefore=1, spaceAfter=4),
        "body": ParagraphStyle("body", fontName="Inter", fontSize=9.7, leading=13.5, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=6),
        "li": ParagraphStyle("li", fontName="Inter", fontSize=9.6, leading=13.1, textColor=INK, leftIndent=12, spaceAfter=3.2),
        "small": ParagraphStyle("small", fontName="Inter", fontSize=8.3, leading=11.4, textColor=MUTED, spaceAfter=3),
        "td": ParagraphStyle("td", fontName="Inter", fontSize=8.5, leading=11.6, textColor=INK),
        "tdB": ParagraphStyle("tdB", fontName="Inter-Semi", fontSize=8.5, leading=11.6, textColor=INK),
        "boxTitle": ParagraphStyle("boxTitle", fontName="Inter-Bold", fontSize=8.5, leading=11, textColor=INK),
        "boxBody": ParagraphStyle("boxBody", fontName="Inter", fontSize=9.1, leading=12.5, textColor=INK),
    }


def header_footer(c, doc):
    if doc.page == 1:
        return
    c.saveState()
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.rect(0, H - 11 * mm, W, 11 * mm, fill=1, stroke=0)
    c.setFillColor(HexColor("#E6E0D4"))
    c.setFont("Inter", 8)
    c.drawString(16 * mm, H - 6.8 * mm, "Тумэн Тур  ·  логотип")
    c.drawRightString(W - 16 * mm, H - 6.8 * mm, "tumentur.ru")
    c.setFillColor(LINE)
    c.rect(0, 0, W, 11 * mm, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont("Inter", 8)
    c.drawString(16 * mm, 4.8 * mm, "15 сентября 2026  ·  правка: Алтай и Монголия")
    c.drawRightString(W - 16 * mm, 4.8 * mm, str(doc.page))
    c.restoreState()


def cover(c, doc):
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.rect(0, 0, 7 * mm, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#D7C4A6"))
    c.setFont("Inter-Semi", 9)
    c.drawString(22 * mm, H - 40 * mm, "ТЗ НА ЗНАК  ·  ТУМЭН ТУР")
    y = H - 58 * mm
    c.setFillColor(white)
    c.setFont("NotoSerif-Bold", 24)
    for line in ["Сейчас Байкал.", "Дальше — Алтай", "и Монголия.", "Знак с этим."]:
        c.drawString(22 * mm, y, line)
        y -= 11 * mm
    y -= 4 * mm
    c.setStrokeColor(HexColor("#D7C4A6"))
    c.setLineWidth(0.8)
    c.line(22 * mm, y, 78 * mm, y)
    y -= 16 * mm
    c.setFillColor(HexColor("#E6E0D4"))
    c.setFont("Inter", 11)
    c.drawString(22 * mm, y, "Контур озера — с сайта. Горы не выкидывать из системы.")
    c.setFillColor(HexColor("#9AA6B4"))
    c.setFont("Inter", 9)
    c.drawString(22 * mm, 26 * mm, "Туры, экскурсии, трансферы  ·  Иркутск")
    c.restoreState()


def P(text, key):
    return Paragraph(text, S()[key])


def tbl(rows, widths):
    data = []
    for i, row in enumerate(rows):
        if i == 0:
            data.append([P(f"<font color='#FBF8F3'><b>{c}</b></font>", "td") for c in row])
        else:
            data.append([P(c, "tdB" if j == 0 else "td") for j, c in enumerate(row)])
    t = Table(data, colWidths=widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
    ]
    for r in range(1, len(rows), 2):
        cmds.append(("BACKGROUND", (0, r), (-1, r), CARD))
    t.setStyle(TableStyle(cmds))
    return t


def build():
    cw = W - 32 * mm
    story = [Spacer(1, 1), PageBreak()]

    story.append(P("0. Что не учли в прошлом ТЗ", "h1"))
    story.append(Callout(
        "Прямой ответ: нет, Алтай и Монголию как будущие направления не заложили.",
        "Прошлый PDF описал компанию как «туры и трансферы на Байкал» и объявил горы браком: «география озёрная, знак говорит горный клуб», «провал = горы / лыжи». Монголия мелькнула только как Хубсугул рядом с Байкалом. Алтая в тексте не было. Это ошибка брифа, не вкуса.",
        "warn",
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(P(
        "Сейчас продают Байкал: туры, экскурсии, трансферы, встреча в Иркутске. Дальше те же услуги на Алтай и в Монголию. Значит система знака не может быть «только озеро навсегда». Горы понадобятся как продукт (Алтай; в Монголии тоже горы и Хубсугул), а не как альпийский бейдж из генератора.",
        "body",
    ))
    story.append(P(
        "Что из прошлого ТЗ остаётся верным: стопка «Альпы + компас + птица + блик + озеро сбоку» — плохой знак. Фото снежных Альп в круге и латиница TUMEN — ставить нельзя. Контур Байкала с сайта — единственный свой актив; его не выдумывать заново.",
        "body",
    ))

    story.append(P("1. Что плохо в логотипе на сайте", "h1"))
    story.append(P(
        "В шапке эмблема и текст «Тумэн Тур / Туры и трансферы на Байкал». Эмблема: вершины, компас, птица, блик, сбоку контур Байкала.",
        "body",
    ))
    try:
        img = Image(LOGO, width=52 * mm, height=40 * mm, kind="proportional")
        box = Table(
            [[img, P(
                "Свой только синий контур озера: ровный, уже читается как Байкал. Его не перерисовывать «от руки» в колбасу и не сглаживать до какашки. Горы на знаке — Альпы из конструктора, не Алтай и не Хамар-Дабан. Они плохо нарисованы и плохо стоят в стопке, но сама идея «горы будут нужны» — верная.",
                "body",
            )]],
            colWidths=[56 * mm, cw - 56 * mm],
        )
        box.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 8),
            ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ]))
        story.append(box)
        story.append(Spacer(1, 3 * mm))
    except Exception:
        pass

    for x in [
        "Шесть смыслов сразу. На 40 px в шапке всё сливается. Сильный знак несёт один главный силуэт, остальные — линейка продуктов.",
        "Контур Байкала пришит сбоку. В favicon и Telegram он пропадает. Его надо сделать самим знаком, не наклейкой.",
        "Горы нарисованы как Альпы + компас + птица. Это конструктор outdoor, не «мы поедем на Алтай». Выкидывать горы из всей системы нельзя — выкинуть стопку и чужую географию.",
        "Имени в эмблеме нет. Без подписи это не «Тумэн Тур».",
        "Для чека от 76 000 ₽ клипарт дешевле текста сайта.",
    ]:
        story.append(P("•  " + x, "li"))

    story.append(Spacer(1, 2 * mm))
    story.append(Callout(
        "Итог по сайту",
        "Контур озера снять с текущего PNG и сделать знаком. Компас, птицу, блик, альпийские зубцы — убрать из эмблемы. Горы оставить в системе как будущий знак направления «Алтай», не как вторую вершину в том же бейдже.",
        "fact",
    ))

    story.append(PageBreak())
    story.append(P("2. Что плохо на предложенных макетах", "h1"))
    story.append(P(
        "Круг, две вершины домиком, «ТУМЭН / ТУР» или TUMEN TUR, риски компаса, фото снежных гор, кепка.",
        "body",
    ))
    for x in [
        "Это генератор outdoor, не оператор с Байкалом и будущим Алтаем.",
        "Снежные пики на макетах — Альпы / Канада. Это не Алтай и не Байкал. Фото в круге — не логотип.",
        "Латиница TUMEN слабее кириллицы и путается с Тюменью. Опечатка TUMEN TURR — мудборд.",
        "«ТУР» между линейками — отель. Тонкие штрихи умрут в печати.",
        "Девять стилей — не система. Макеты не взяли готовый контур Байкала с сайта.",
    ]:
        story.append(P("•  " + x, "li"))
    story.append(Spacer(1, 2 * mm))
    story.append(Callout(
        "Итог по макетам",
        "Не ставить. Горы на макетах не закрывают задачу «потом Алтай»: это чужие Альпы. Нужна семья знаков, не ещё один круг с двумя пиками.",
        "dont",
    ))

    story.append(P("3. Каким сделать — сейчас и потом", "h1"))
    story.append(Callout(
        "Сейчас (Байкал)",
        "Знак = контур озера с сайта, как есть (векторизовать, не придумывать новый силуэт). Рядом кириллица «Тумэн Тур». Один плоский тёмно-байкальский сине-зелёный. Подпись «Туры и трансферы на Байкал» снаружи, её потом можно сменить.",
        "do",
    ))
    story.append(Spacer(1, 2.5 * mm))
    story.append(Callout(
        "Потом (Алтай и Монголия)",
        "Те же туры, экскурсии, трансферы. Имя и цвет не менять. Подпись снаружи: «Байкал · Алтай · Монголия» или три направления на сайте. Отдельные пиктограммы линейки: Алтай — свой упрощённый хребет (не Альпы, не буква M в круге); Монголия — не юрта-клипарт и не орда. Не складывать озеро + горы + степь в одну эмблему. Одно имя, три продукта.",
        "do",
    ))
    story.append(Spacer(1, 3 * mm))

    try:
        k = Image(KONTUR, width=48 * mm, height=48 * mm, kind="proportional")
        box = Table(
            [[k, P(
                "Это контур с tumentur.ru, снятый с эмблемы. Его и утверждать первым: чёрный, 40 мм, белое поле. Не сглаживать в галочку и не утолщать в «какашку». Мелкие заливы, которые умрут на 24 px, можно чуть закрыть, не меняя жест.",
                "body",
            )]],
            colWidths=[52 * mm, cw - 52 * mm],
        )
        box.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 8),
        ]))
        story.append(box)
        story.append(Spacer(1, 3 * mm))
    except Exception:
        pass

    story.append(P("Имя и цвет", "h2"))
    story.append(P(
        "«Тумэн Тур», буква Э. Свой гротеск, не Arial/Inter как есть. Латиница запасная: одно слово Tumentur. Цвет знака — один, тёмная вода. Оранжевый — кнопке сайта. Четыре файла: цвет, чёрный, белый, инверсия.",
        "body",
    ))
    story.append(P("Комплект сейчас", "h2"))
    story.append(tbl(
        [
            ["Где", "Что стоит"],
            ["Шапка, бланк", "Контур с сайта + «Тумэн Тур». Подпись про Байкал — снаружи, временная."],
            ["Пост 1:1", "Контур сверху, имя снизу."],
            ["Telegram, favicon", "Только контур. На 16 px он станет галочкой — имя в шапке чата обязательно."],
            ["Табличка в аэропорту", "Имя ≥ 40 мм, высокий контраст, с 5 метров."],
            ["Позже: страница Алтай", "Тот же wordmark + пиктограмма Алтая. Не новый логотип компании."],
            ["Позже: Монголия", "Тот же wordmark + свой знак направления. Не юрта вместо Байкала."],
        ],
        [48 * mm, cw - 48 * mm],
    ))

    story.append(Spacer(1, 4 * mm))
    story.append(P("Как принимать", "h2"))
    for i, x in enumerate([
        "Чёрный контур с сайта, 40 мм на белом. Если это не тот силуэт, что на эмблеме tumentur.ru — переделать.",
        "Не какашка, не колбаса, не выдуманная галочка. Не Альпы в круге.",
        "Восемь человек, 5 секунд, знак без имени. Нужно: озеро / Байкал / туры. Провал: лыжный курорт, Альпы, Тюмень, фекалия. Слово «горы» само по себе не провал — провал чужая альпийская картинка.",
        "Рядом ББТ, КроссТур, Добрый Байкал, Байкалика — не быть «ещё одним из них».",
        "Печать в одну краску. Потом цвет. Горы Алтая не рисовать в этом же знаке «на вырост».",
    ], 1):
        story.append(P(f"{i}.  {x}", "li"))

    story.append(Spacer(1, 3 * mm))
    story.append(Callout(
        "Не утверждать",
        "Новый силуэт «похожий на Байкал». Стопку озеро+Альпы+компас. Фото в круге. TUMEN TUR. Один бейдж «Байкал-Алтай-Монголия». Лист из девяти стилей.",
        "dont",
    ))
    story.append(Spacer(1, 2 * mm))
    story.append(P(
        "Дизайнеру: этот PDF, PNG эмблемы с сайта, файл контура brand/tumen-tur/source/site-baikal-mask.png, промпт docs/tumen-tur-prompt-ii-dizajner.md. Сдать: SVG контура, четыре комплекта × четыре цвета, 16–32 px. Пиктограммы Алтая и Монголии — отдельным этапом, в той же сетке и цвете.",
        "small",
    ))

    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=18 * mm, bottomMargin=16 * mm,
        title="Логотип Тумэн Тур — Байкал, Алтай, Монголия",
        author="Бриф",
        subject="Знак: контур с сайта; горы в системе на потом",
    )
    doc.build(story, onFirstPage=cover, onLaterPages=header_footer)
    print(OUT)


if __name__ == "__main__":
    build()
