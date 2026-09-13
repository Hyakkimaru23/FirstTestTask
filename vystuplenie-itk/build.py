#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Два отдельных выступления ИТК: Никита (тема 16) и Таисья (тема 18)."""

from pathlib import Path
import shutil
import subprocess
import zipfile

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from pptx import Presentation
from pptx.dml.color import RGBColor as PRGB
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn as pqn
from pptx.util import Inches as PInches, Pt as PPt
from lxml import etree

OUT = Path("/workspace/vystuplenie-itk")
ART = Path("/opt/cursor/artifacts/vystuplenie-itk")
DL = OUT / "download"
OUT.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)
DL.mkdir(parents=True, exist_ok=True)

INK = RGBColor(0x11, 0x11, 0x11)
P_INK = PRGB(0x11, 0x11, 0x11)
P_ACCENT = PRGB(0xC2, 0x41, 0x0C)
P_DARK = PRGB(0x1C, 0x19, 0x17)
P_WHITE = PRGB(0xFF, 0xFF, 0xFF)
P_MUTED = PRGB(0x3F, 0x3F, 0x46)


# ---------- Word helpers ----------
def set_run_font(run, name="Arial", size=14, bold=False, color=INK):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color


def add_page_number(section):
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("не читать с листа целиком — это страховка   ·   ")
    set_run_font(run, size=9, color=RGBColor(0x33, 0x33, 0x33))
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    r = p.add_run()
    r._r.append(fld1)
    r2 = p.add_run()
    r2._r.append(instr)
    r3 = p.add_run()
    r3._r.append(fld2)
    set_run_font(r, size=9)
    set_run_font(r2, size=9)
    set_run_font(r3, size=9)


def setup_doc(doc, header_text):
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = hp.add_run(header_text)
    set_run_font(run, size=9, color=RGBColor(0x33, 0x33, 0x33))
    add_page_number(section)
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(14)
    style.font.color.rgb = INK
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    pf = style.paragraph_format
    pf.space_after = Pt(6)
    pf.space_before = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT


def p(doc, text, size=14, bold=False, space_after=8, space_before=0, center=False):
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(space_after)
    para.paragraph_format.space_before = Pt(space_before)
    para.paragraph_format.line_spacing = 1.3
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
    parts = text.split("**")
    for i, part in enumerate(parts):
        if not part:
            continue
        run = para.add_run(part)
        set_run_font(run, size=size, bold=bold or (i % 2 == 1))
    return para


def h(doc, text, size=16):
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(14)
    para.paragraph_format.space_after = Pt(8)
    para.paragraph_format.line_spacing = 1.15
    run = para.add_run(text)
    set_run_font(run, size=size, bold=True)
    return para


def cue(doc, text):
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(4)
    para.paragraph_format.space_after = Pt(2)
    run = para.add_run(text)
    set_run_font(run, size=11, bold=True, color=RGBColor(0x33, 0x33, 0x33))
    return para


def line(doc):
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(4)
    para.paragraph_format.space_after = Pt(4)
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "111111")
    pBdr.append(bottom)
    para._p.get_or_add_pPr().append(pBdr)


SOURCES_COMMON = [
    ("BLS, Establishment Age and Survival / TED",
     "https://www.bls.gov/bdm/bdmage.htm",
     "когорты новых заведений США; первый год ≈ каждый пятый исчезает; это заведения, не «прогоревшие фирмы»"),
    ("ТАСС, 26.05.2026, исследование «Точка банка»",
     "https://news.mail.ru/economics/71021631/",
     "из открытых в 2022 к концу 2025 живы ≈ 50%; из открытых в 2020 через 5 лет ≈ 42%"),
    ("«Коммерсантъ», 26.05.2026, то же исследование Точки",
     "https://www.kommersant.ru/doc/8690067",
     "подтверждение порядка цифр 50% / 42%"),
    ("FinExpertiza по данным ФНС, 2025 (Известия / Frank Media)",
     "https://frankmedia.ru/258162",
     "около 88% ликвидаций юрлиц — исключение налоговой; не путать с живым ИП"),
]

SOURCES_NIKITA = SOURCES_COMMON + [
    ("2ГИС / «Коммерсантъ» о рынке кофеен",
     "https://www.kommersant.ru/doc/8361125",
     "плотность и смена форматов общепита; не цифра «закрытий в Иркутске»"),
    ("Материалы о конкуренции одинаковых карточек на маркетплейсах",
     "https://www.moysklad.ru/poleznoe/marketplejsy/vse-ottenki-serogo-na-chto-idut-prodavtsy-v-borbe-za-pokupateley-na-marketpleysakh/",
     "новички часто не считают прибыль, конкурируют скидкой"),
]

SOURCES_TAISIYA = SOURCES_COMMON + [
    ("Росстат, Выборочное наблюдение использования суточного фонда времени, 2019",
     "https://rosstat.gov.ru/",
     "женщины ≈ 18% суток на дом и уход (больше 4 часов), мужчины ≈ 7,8% (меньше 2 часов)"),
    ("РБК Тренды / Tochno.st о неоплачиваемом домашнем труде",
     "https://trends.rbc.ru/trends/social/62ac242b9a79478caa687c8f",
     "«вторая смена»; механизм нехватки часов, не доля закрытий бизнеса"),
]


# ---------- Speeches: each person alone ----------
NIKITA_SPEECH = [
    (1, "ВСТАТЬ · СМОТРЕТЬ В ЗАЛ · не читать шапку целиком", "0:00", [
        "Здравствуйте. **Харитонов Никита Васильевич.** Третий курс, группа 69, специальность «Торговое дело», Иркутский технологический колледж.",
        "Сегодня я говорю **один**. Тема одна.",
        "Почему точка исчезает из реестра не потому что хозяин «слабо старался», а потому что он **вошёл последним** на улицу, где гостей уже разобрали.",
        "Если кто-то из зала слышал фразу **«восемьдесят процентов закрываются в первый год»** — запомните её. Через минуту я её сниму. Потом покажу механизм, который в торговом деле видно глазами.",
    ]),
    (2, "КЛИК · шаг к экрану · палец к зачёркнутой цифре", "0:30", [
        "Эту цифру повторяют на курсах и в роликах. Как приговор.",
        "По живым когортам картина другая.",
        "По данным **«Точка Банка»**, которые в мае 2026 года приводил **ТАСС**: из компаний и ИП, открытых в 2022-м, к концу 2025-го на ногах осталась примерно **половина**. Не один из десяти. Половина.",
        "Я не утверждаю, что «все живут». Я утверждаю: **восемьдесят процентов в первый год — неподтверждённая страшилка.**",
    ]),
    (3, "КЛИК · ПАУЗА после «прогореть»", "1:00", [
        "И ещё важнее. **Исчезнуть из реестра — не всегда значит “прогореть”.**",
        "Человек мог не начать. Уйти в найм. Сменить ИП на ООО. Быть пустой фирмой, которую сняла налоговая.",
        "Закрытие и провал — разные слова. Сегодня я их не путаю.",
        "Моя тема — не про все смерти сразу. Моя тема — про **одну ошибку торговли**: смотреть на чужую очередь и открывать пятую точку на том же проходе.",
    ]),
    (4, "КЛИК · тезис медленно · смотреть в зал", "1:30", [
        "Тезис в одной фразе.",
        "**Даже верный расчёт чеков не спасёт, если вы вошли последними в полный вагон.**",
        "Представьте не «рынок России», а один проход. Пешеходная улица вроде **130-го квартала**. Или линия фуд-корта.",
        "Это фон, который зал узнает. Я не называю закрывшихся иркутских точек и не выдумываю их.",
        "Четыре вывески уже делают почти одно и то же. Кофе. Выпечка. «То же самое, только наше».",
        "Пятая открывается красиво.",
    ]),
    (5, "КЛИК — загорается пятая точка · ПАУЗА", "2:05", [
        "Хозяин смотрит на очередь у соседа и думает: **раз у них забито — будет и у меня.**",
        "Это самообман.",
        "Очередь у соседа не доказывает, что гостей ещё не разобрали. Она доказывает, что гостей **уже разобрали**. В его сторону.",
        "В торговом деле это базовая путаница: спрос, который виден глазами, и спрос, который ещё свободен.",
        "Витрина полная. Поток — нет.",
    ]),
    (6, "КЛИК · три слова по одному", "2:40", [
        "Сосед часто жив не потому что «атмосфера».",
        "У него **аренда со старого договора**. **Свои люди**, которые ходят третий год. **Поставщик**, которому он не чужой.",
        "Новичок копирует витрину. **Экономику не копирует.**",
        "Вы видите стакан и очередь. Не видите цену метра, которая у соседа застыла три года назад. Не видите, что его бариста уже знает половину прохода по именам.",
        "В торговом деле это базовая ошибка: смотреть на чужой оборот и не видеть чужие условия.",
    ]),
    (7, "КЛИК · можно показать телефон как «выдачу»", "3:20", [
        "Та же история без улицы. **Выдача на маркетплейсе.**",
        "Десятки карточек одного товара из одного каталога. Новичок заходит последним.",
        "Покупатель не видит «мою уникальную закупку». Он видит цену, отзывы и кто выше.",
        "Чтобы тебя заметили, площадка продаёт место внутри себя.",
        "Кажется, аренды нет. **Аренда спрятана в комиссии и продвижении.**",
        "Островок в ТЦ — та же песня. Вам продали «проходное место». Не сказали, сколько островков уже режут тот же поток.",
        "Если на площадке уже сорок одинаковых карточек, а я сорок первый с той же закупкой — я не «выхожу на рынок». **Я встаю в хвост выдачи.**",
        "В курилке это звучит иначе: «у них крутится — и у меня крутанётся». Крутится у того, кто уже стоит выше. У новичка крутится рекламный кабинет.",
    ]),
    (8, "КЛИК · считать на пальцах · сказать “условный”", "4:10", [
        "Простой счёт. **Условный. Это не статистика Иркутска.** Это учебная модель. Я это произношу вслух.",
        "На проходе **400** стаканов в день. Четыре точки — по **100**.",
        "Новой, чтобы отбить аренду и смену, нужно, допустим, **90**.",
        "Открывается пятая. Поток не вырос. Его разрезали на пять. Стало по **80**.",
        "На бумаге — «кофейня как у них». В кассе — ниже порога.",
        "Иногда вместе с новой сыпется самая слабая старая.",
        "Одинаковые точки на одном потоке едят не рынок. **Они едят друг друга.**",
    ]),
    (8, "без клика · вывод твёрдо", "4:50", [
        "Вывод. В торговле опоздание — не про лень. Это про место, которое уже занято чужими постоянными и чужой старой арендой.",
        "**«Открою такое же» — не стратегия.** Это вход в вагон, где сидячие места заняты.",
        "Рынок может быть живым. **Моё место в нём — нет.**",
        "Это важно для нашей специальности. Мы учимся считать не чужой оборот в разговоре, а **свою** экономику на чужом потоке.",
    ]),
    (9, "КЛИК · три вопроса по одному", "5:15", [
        "Что смотреть до вывески. Не «как красиво у них», а **три вопроса**.",
        "**Первый.** Сколько гостей на этом проходе ещё не разобрано? Не очередь соседа — свободный хвост потока.",
        "**Второй.** Какая у меня аренда против его старой? Если метр дороже, порог выше. Значит, мне нужно не «как у них», а больше, чем у них.",
        "**Третий.** Чем я не копия? Если ответить нечего, я пятый стакан на том же подносе.",
        "Это не запрет открываться. Это **цена входа.**",
        "Если на все три вопроса ответ «не знаю» — вы ещё не изучали улицу. Вы смотрели витрину.",
    ]),
    (10, "КЛИК · спокойно, без шутки", "6:00", [
        "Как это выглядит через год.",
        "Хозяин говорит: «не пошло». Соседи говорят: «ну, восемьдесят процентов же закрываются».",
        "А правда короче. Пошло у тех, кто стоял раньше. Не пошло у того, кто разрезал чужой поток и не добавил нового.",
        "В реестре это та же строка: **прекратил деятельность**.",
        "Поэтому цифра «80%» удобна. Она прячет конкретную ошибку за общей страшилкой.",
    ]),
    (11, "КЛИК · один вопрос · смотреть в зал", "6:40", [
        "Что забрать с собой. Один вопрос, не десять заповедей.",
        "**Прежде чем копировать чужую точку — спросить, сколько гостей на этом проходе ещё не разобрано.**",
        "Если ответ «не знаю, но у них очередь» — это не исследование. Это надежда.",
        "Надежда не платит аренду.",
        "Полный вагон не становится свободным от того, что вы купили красивую вывеску.",
        "Я не говорю «не открывайте». Я говорю: сначала посчитайте свободный хвост потока. Потом вывеску.",
    ]),
    (13, "КЛИК · СМОТРЕТЬ В ЗАЛ", "7:20", [
        "**Спасибо. Вопросы.**",
    ]),
]


NIKITA_QA = [
    ("Откуда вы взяли, что 80% — миф?",
     "Эту цифру повторяют без когорты. У BLS за первый год исчезает примерно каждый пятый новое заведение, не восемь из десяти. В России Точка Банк / ТАСС: из открытых в 2022 к концу 2025 живы около половины. Я не утверждаю «все живут». Я утверждаю: 80% в первый год — неподтверждённая страшилка."),
    ("Это же не ваше исследование?",
     "Да. Это учебный доклад, не полевое исследование группы 69. Я беру открытые источники и один механизм. Тема «забитая улица» — жизненная ось, не измеренная причина номер один. Это написано в справке для преподавателя."),
    ("При чём тут торговое дело?",
     "Потому что торговля копирует глазами: витрину соседа, карточку на маркетплейсе, островок в ТЦ. Специальность как раз про то, что оборот соседа — не ваша экономика."),
    ("Вы против того, чтобы открывать бизнес?",
     "Нет. Я против входа в полный вагон без счёта. Это не запрет. Это цена."),
    ("Почему не про налоги и ключевую ставку?",
     "Это реальные давления 2025–2026. Я сознательно взял одну человеческую и торговую ось, которая на налогах не закрывается. Иначе доклад снова станет «во всём виновата эпоха»."),
    ("Это про Иркутск или «вообще»?",
     "Механизм общий. 130-й квартал и фуд-корт — фон, который зал узнает. Я не называл закрывшихся иркутских точек и не выдумывал их. Счёт 400 стаканов — учебная модель, я это произношу вслух."),
    ("А если ниша новая, не пятая кофейня?",
     "Тогда сторона «забитой улицы» слабее. Остаётся вопрос: как быстро копии заполнят выдачу. Даже новая ниша на маркетплейсе быстро обрастает одинаковыми карточками."),
]


TAISIYA_SPEECH = [
    (1, "ВСТАТЬ · СМОТРЕТЬ В ЗАЛ · не читать шапку целиком", "0:00", [
        "Здравствуйте. **Карнаухова Таисья Петровна.** Третий курс, группа 69, специальность «Торговое дело», Иркутский технологический колледж.",
        "Сегодня я говорю **одна**. Тема одна.",
        "Не витрина и не аренда. Почему живое дело иногда закрывают, **когда рынок его ещё не тронул.**",
        "Если вы слышали, что **«восемьдесят процентов закрываются в первый год»** — эту цифру я тоже сниму. Не чтобы пугать другой статистикой. Чтобы показать: в одной графе «закрылись» прячутся разные смерти. Сегодня — та, которую **не видно с улицы.**",
    ]),
    (2, "КЛИК · шаг к экрану · палец к зачёркнутой цифре", "0:30", [
        "Цифру «80%» повторяют как приговор.",
        "По данным **«Точка Банка»**, которые в мае 2026 года приводил **ТАСС**: из компаний и ИП, открытых в 2022-м, к концу 2025-го на ногах осталась примерно **половина**. Не один из десяти.",
        "Я не утверждаю, что «все живут». Я утверждаю: восемьдесят процентов в первый год — **страшилка без когорты.**",
    ]),
    (3, "КЛИК · ПАУЗА после «прогореть»", "0:55", [
        "Исчезнуть из реестра — не всегда значит **«прогореть».**",
        "Не начал. Ушёл в найм. Сменил форму. Пустая фирма, которую сняла налоговая.",
        "И ещё один случай, про который реже говорят вслух.",
        "Человек закрыл ИП, **чтобы сохранить мир дома.**",
        "В отчёте это выглядит так же, как провал на аренде. Живьём — нет.",
        "Моя тема — про эту смерть. Не про «девушек, которым не дано». **Про часы.**",
    ]),
    (4, "КЛИК · тезис медленно", "1:30", [
        "Тезис.",
        "**Дело иногда закрывают не потому что нет спроса. А потому что у бизнеса остатки часов, а у дома — полный день.**",
        "Спрос может быть. Клиенты могут писать. Касса в отдельные дни даже радует.",
        "Не хватает не идеи. **Не хватает суток.**",
    ]),
    (5, "КЛИК · тише, ближе к залу", "1:55", [
        "Вечер. Телефон: клиент просит перенести заказ, ответить, выйти.",
        "В соседней комнате: магазин, ребёнок, **«ты же дома — значит свободен».**",
        "**Клиент подождёт. Дом не подождёт.**",
        "Один вечер — ерунда. Тридцать таких вечеров — дыра в ответах, в закупках, в голове.",
        "Закупку переносят. На отзыв не отвечают. Постоянный уходит не всегда к конкуренту. Он уходит в тишину.",
        "В торговле тишина убивает быстрее плохой витрины. Карточка без ответа — мёртвая карточка. Точка без человека в чате — пустая точка.",
        "Покупатель не пишет в отзыве «у продавца дома болел ребёнок». Он пишет «не отвечает». И уходит.",
    ]),
    (6, "КЛИК · не извиняться за цифру, назвать год", "2:40", [
        "Это не лень и не «слабый характер».",
        "По выборочному наблюдению **Росстата 2019 года** женщины в среднем отдавали дому и уходу **больше четырёх часов** в сутки. Мужчины — **меньше двух**.",
        "Цифра старая. Год надо назвать. Направление с тех пор не перевернулось.",
        "Тема **не про “девушек”**. Тема про любого, на ком висит вторая смена без зарплаты.",
        "Мужчина с больными родителями попадает в ту же мясорубку. Просто чаще эту смену вешают на тех, кто «и так дома».",
        "Я не утверждаю, что семья — причина номер один по статистике. Такой доли в официальных таблицах нет. **Я её не выдумаю.**",
    ]),
    (7, "КЛИК · схема суток · палец к «дело?»", "3:25", [
        "Сон. Учёба или смена. Дом. На своё дело остаются **обрезки**.",
        "Сложные закупки и живые покупатели в обрезках не живут.",
        "Идея может быть живой. **Человек уже нет.**",
        "Это не “она не предприниматель”. Это арифметика суток. Кому повесили дом — у того дело сидит в обрезках. Пол не при чём. **Часы при чём.**",
    ]),
    (8, "КЛИК · связать с торговлей", "4:00", [
        "Почему это про **торговое дело**, а не «просто семья».",
        "Торговля держится на ответах. На приёмке. На том, что ты вечером пересчитал остаток и утром не обманул покупателя.",
        "Если вечер съеден домом, утром карточка врёт. Врёт остаток. Врёт срок. Врёт «сейчас отправлю».",
        "Покупатель не знает про вашу семью. Он знает, что ему не ответили.",
        "Рынок ещё не начал убивать. **Убивает календарь.**",
    ]),
    (9, "КЛИК · ПАУЗА после “прекратил деятельность”", "4:40", [
        "Через год ИП закрывают, чтобы **сохранить мир**. Меньше ссор. Меньше «опять ты в телефоне». Меньше риска.",
        "В реестре это строка: **прекратил деятельность**.",
        "Рядом с тем, кто прогорел на аренде.",
        "А здесь рынок ещё не начал убивать. Убили календарь и стыд: «я плохой сын, плохая мать, плохой партнёр, раз думаю о кассе».",
        "Стыд удобный. Он позволяет сказать «не пошло», не говоря **«мне не дали часов».**",
    ]),
    (10, "КЛИК · не повышать голос", "5:20", [
        "Если спрос есть, а часов нет — это не «не судьба».",
        "Это конфликт двух честных желаний. Семья хочет безопасности. Дело хочет времени.",
        "Нельзя победить советом **«просто будь жёстче»**.",
        "Жёсткость без договорённости ломает дом. Мягкость без границ ломает дело.",
        "**Выбор есть. Бесплатного выбора нет.**",
    ]),
    (10, "без клика · ловушка “гибкости”", "5:50", [
        "Ещё одна ловушка нашей специальности.",
        "Кажется, своё дело «гибкое». Сидишь дома — значит, успеешь и кассу, и суп.",
        "Гибкость без границ превращается в две полные смены. Одна оплачивается плохо. Вторая не оплачивается вовсе.",
        "Поэтому «буду торговать с телефона вечером» звучит легко на паре. В быту это **третья смена** после учёбы и дома.",
        "Если третьей смены нет в сутках, лучше не обещать её рынку.",
        "На паре «гибкий график» звучит как свобода. В быту это часто значит: дело живёт в щелях между чужими просьбами.",
    ]),
    (11, "КЛИК · один разговор · смотреть в зал", "6:25", [
        "Что забрать. Один разговор **до** открытия, не после похорон ИП.",
        "**Прежде чем открывать своё — честно сказать, у кого в семье какие часы.**",
        "Не «поддержишь меня?» — это пустое. А кто забирает ребёнка в среду. Кто отвечает на отзыв после десяти. Кто готов, что касса будет жить в общей комнате.",
        "Если часов нет, реестр рано или поздно оформит то, что дом уже закрыл.",
        "Это не запрет. Это цена. Её лучше назвать вслух, пока вывески ещё нет.",
        "Если в семье все кивают и никто не называет день недели — часов нет. Есть только вежливое «поддержим».",
    ]),
    (11, "без клика · финал твёрдо", "7:05", [
        "Пока все закрытия сваливают в «восемьдесят процентов обречены», не видно тех, кого сняли ещё на кухне.",
        "Их нельзя вылечить советом «открой такое же, только старайся больше».",
        "Их нельзя вылечить и советом «забей на дом». Дом потом выставит счёт дороже любой аренды.",
        "Поэтому мой доклад не про «как стать жёстче». Он про то, чтобы **назвать цену часов** до того, как касса переедет в общую комнату.",
    ]),
    (13, "КЛИК · СМОТРЕТЬ В ЗАЛ", "7:30", [
        "**Спасибо. Вопросы.**",
    ]),
]


TAISIYA_QA = [
    ("Откуда вы взяли, что 80% — миф?",
     "Эту цифру повторяют без когорты. У BLS за первый год исчезает примерно каждый пятый новое заведение, не восемь из десяти. В России Точка Банк / ТАСС: из открытых в 2022 к концу 2025 живы около половины. Я не утверждаю «все живут». Я утверждаю: 80% в первый год — неподтверждённая страшилка."),
    ("Это же не ваше исследование?",
     "Да. Это учебный доклад, не полевое исследование группы 69. Тема «дом съедает дело» — жизненная ось и сцена, не измеренная причина номер один. Доли «закрылись из-за семьи» в официальной статистике нет. Я её не выдумываю. Это написано в справке для преподавателя."),
    ("Почему блок про семью на паре по торговле? Это не экономика.",
     "В реестре закрытое ИП выглядит одинаково. Если часть “смертей” — это часы и быт, а мы ищем вину в витрине, мы лечим не ту болезнь. Для торговли это практично: точка без человека, который на неё отвечает, тоже пустая."),
    ("Вы хотите сказать, что девушки не созданы для бизнеса?",
     "Нет. Тема не про пол и не про характер. Тема про часы. Росстат 2019 показывает перекос второй смены, но в ту же мясорубку попадает любой, на ком висит дом. Пол не при чём. Часы при чём."),
    ("Почему не про налоги и ключевую ставку?",
     "Это реальные давления 2025–2026. Я сознательно взяла одну человеческую ось, которая на налогах не закрывается. Иначе доклад снова станет «во всём виновата эпоха»."),
    ("Нет доли в статистике — тогда зачем эта тема?",
     "Потому что графа «закрылись» прячет разные смерти. Если мы все их сваливаем в миф про 80%, мы не видим тех, кого сняли ещё на кухне. Учебный доклад как раз про механизм, который статистика не режет отдельно."),
    ("Что делать, если часов нет?",
     "Не открывать «в обрезках» и не обещать рынку третью смену, которой нет в сутках. Либо договариваться о часах вслух до вывески. Я не даю волшебного совета «будь жёстче»: жёсткость без договорённости ломает дом."),
]


def add_sources_section(doc, sources):
    h(doc, "Источники и оговорки", 16)
    p(doc, "Закрытие записи в реестре не равно провалу живого дела. Тема доклада — механизм и сцены, не рейтинг причин по официальной статистике.", 13)
    p(doc, "Цифры, которые сознательно НЕ произносим как факт: «80% в первый год»; «75% ООО / 65% ИП через год»; «82% из-за cash flow»; проценты CB Insights и Вассермана как будто про ИП в Иркутске.", 13)
    for title, url, note in sources:
        p(doc, f"{title}. {note} Дата обращения: 13.09.2026. {url}", 12)


def word_count(speech):
    words = 0
    for *_, paras in speech:
        for para in paras:
            words += len(para.replace("**", "").split())
    return words


def build_full(meta):
    doc = Document()
    setup_doc(doc, meta["header_full"])
    p(doc, "ГАПОУ ИО «Иркутский технологический колледж» (ИТК)", 14, bold=True, center=True, space_after=2)
    p(doc, "Специальность 38.02.08 «Торговое дело»  ·  3 курс  ·  группа 69", 13, center=True, space_after=2)
    p(doc, meta["fio"], 14, bold=True, center=True, space_after=2)
    p(doc, "Отдельное выступление  ·  один докладчик", 13, center=True, space_after=8)
    p(doc, meta["title1"], 16, bold=True, center=True, space_after=0)
    p(doc, meta["title2"], 16, bold=True, center=True, space_after=8)
    p(doc, meta["hall"], 13, center=True)
    p(doc, "Дата: «____» сентября 2026 г.  ·  Иркутск  ·  регламент 8–10 мин + вопросы", 12, center=True, space_after=12)
    line(doc)
    h(doc, "Как пользоваться этим файлом", 16)
    p(doc, "Это страховка, не сценарий “читать каждую букву”. Жирным — удар голосом. Квадратные скобки — время. Строки ПАУЗА / КЛИК — действия, их не произносить.")
    p(doc, "Это отдельное выступление. Второго докладчика на сцене нет. Кликает тот, кто говорит — то есть вы.")
    h(doc, "Оглавление", 16)
    for t in meta["toc"]:
        p(doc, t, 13, space_after=2)
    line(doc)

    last = None
    for slide, cues, time, paras in meta["speech"]:
        section = meta["section_for"](slide, paras)
        if section and section != last:
            h(doc, section, 16)
            last = section
        cue(doc, f"[{time}]   СЛАЙД {slide}   ·   {cues}")
        for para in paras:
            p(doc, para, 14)

    h(doc, "Вопросы преподавателю — не читать с листа", 16)
    p(doc, "Короткие честные ответы. Если не знаем долю — так и говорим.")
    for i, (q, a) in enumerate(meta["qa"], 1):
        p(doc, f"{i}. {q}", 13, bold=True, space_after=2)
        p(doc, a, 13)
    add_sources_section(doc, meta["sources"])
    path = OUT / meta["full_name"]
    doc.save(path)
    return path


def build_full_pdf(meta):
    """Readable A4 PDF of the same full script. LibreOffice Writer is broken here."""
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    pdfmetrics.registerFont(TTFont("Sans", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("SansBold", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"))

    def md(text):
        # **bold** -> <b>
        out = []
        parts = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").split("**")
        for i, part in enumerate(parts):
            out.append(f"<b>{part}</b>" if i % 2 == 1 else part)
        return "".join(out)

    styles = {
        "center_b": ParagraphStyle("cb", fontName="SansBold", fontSize=12, leading=16, alignment=TA_CENTER, textColor="#111111", spaceAfter=4),
        "center": ParagraphStyle("c", fontName="Sans", fontSize=11, leading=15, alignment=TA_CENTER, textColor="#111111", spaceAfter=4),
        "title": ParagraphStyle("t", fontName="SansBold", fontSize=14, leading=18, alignment=TA_CENTER, textColor="#111111", spaceAfter=6),
        "h": ParagraphStyle("h", fontName="SansBold", fontSize=13, leading=17, alignment=TA_LEFT, textColor="#111111", spaceBefore=12, spaceAfter=6),
        "cue": ParagraphStyle("cue", fontName="SansBold", fontSize=10, leading=13, alignment=TA_LEFT, textColor="#333333", spaceBefore=6, spaceAfter=2),
        "body": ParagraphStyle("b", fontName="Sans", fontSize=12, leading=17, alignment=TA_LEFT, textColor="#111111", spaceAfter=6),
        "small": ParagraphStyle("s", fontName="Sans", fontSize=10, leading=14, alignment=TA_LEFT, textColor="#111111", spaceAfter=5),
        "footer": ParagraphStyle("f", fontName="Sans", fontSize=8, leading=10, alignment=TA_CENTER, textColor="#333333"),
    }

    path = OUT / meta["full_name"].replace(".docx", ".pdf")
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title=meta["fio"], author=meta["fio"],
    )
    story = []
    story.append(Paragraph("ГАПОУ ИО «Иркутский технологический колледж» (ИТК)", styles["center_b"]))
    story.append(Paragraph("Специальность 38.02.08 «Торговое дело»  ·  3 курс  ·  группа 69", styles["center"]))
    story.append(Paragraph(meta["fio"], styles["center_b"]))
    story.append(Paragraph("Отдельное выступление  ·  один докладчик", styles["center"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(meta["title1"], styles["title"]))
    story.append(Paragraph(meta["title2"], styles["title"]))
    story.append(Paragraph(meta["hall"], styles["center"]))
    story.append(Paragraph("Дата: «____» сентября 2026 г.  ·  Иркутск  ·  регламент 8–10 мин + вопросы", styles["center"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Как пользоваться этим файлом", styles["h"]))
    story.append(Paragraph("Это страховка, не сценарий “читать каждую букву”. Жирным — удар голосом. Квадратные скобки — время. Строки ПАУЗА / КЛИК — действия, их не произносить.", styles["body"]))
    story.append(Paragraph("Это отдельное выступление. Второго докладчика на сцене нет. Кликает тот, кто говорит — то есть вы.", styles["body"]))
    story.append(Paragraph("Оглавление", styles["h"]))
    for t in meta["toc"]:
        story.append(Paragraph(t, styles["body"]))

    last = None
    for slide, cues, time, paras in meta["speech"]:
        section = meta["section_for"](slide, paras)
        if section and section != last:
            story.append(Paragraph(section, styles["h"]))
            last = section
        story.append(Paragraph(f"[{time}]   СЛАЙД {slide}   ·   {cues}", styles["cue"]))
        for para in paras:
            story.append(Paragraph(md(para), styles["body"]))

    story.append(Paragraph("Вопросы преподавателю — не читать с листа", styles["h"]))
    story.append(Paragraph("Короткие честные ответы. Если не знаем долю — так и говорим.", styles["body"]))
    for i, (q, a) in enumerate(meta["qa"], 1):
        story.append(Paragraph(f"{i}. {q}", styles["h"]))
        story.append(Paragraph(a, styles["small"]))
    story.append(Paragraph("Источники и оговорки", styles["h"]))
    story.append(Paragraph("Закрытие записи в реестре не равно провалу живого дела. Тема доклада — механизм и сцены, не рейтинг причин по официальной статистике.", styles["small"]))
    story.append(Paragraph("Цифры, которые сознательно НЕ произносим как факт: «80% в первый год»; «75% ООО / 65% ИП через год»; «82% из-за cash flow»; проценты CB Insights и Вассермана как будто про ИП в Иркутске.", styles["small"]))
    for title, url, note in meta["sources"]:
        story.append(Paragraph(f"{title}. {note} Дата обращения: 13.09.2026. {url}", styles["small"]))

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Sans", 8)
        canvas.setFillColorRGB(0.2, 0.2, 0.2)
        canvas.drawCentredString(A4[0] / 2, 1.2 * cm, f"не читать с листа целиком — это страховка   ·   {doc_.page}")
        canvas.drawString(2 * cm, A4[1] - 1.2 * cm, meta["header_full"])
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return path


def build_cards(meta):
    doc = Document()
    setup_doc(doc, meta["header_cards"])
    p(doc, f"Карточки. {meta['who']}", 16, bold=True, center=True)
    p(doc, "Держать в руках. Один блок — одна мысль. Если проектор умер — вести только отсюда.", 13, center=True)
    p(doc, "Это ваше отдельное выступление. На сцене только вы.", 13, center=True)
    line(doc)
    for n, (slide, cues, time, paras) in enumerate(meta["speech"], 1):
        h(doc, f"Блок {n}   ·   слайд {slide}   ·   {time}", 16)
        cue(doc, cues)
        for para in paras:
            p(doc, para, 16, space_after=10)
        line(doc)
    path = OUT / meta["cards_name"]
    doc.save(path)
    return path


def build_teacher():
    doc = Document()
    setup_doc(doc, "Справка для преподавателя  ·  группа 69  ·  ИТК  ·  два отдельных доклада")
    p(doc, "Справка для преподавателя", 16, bold=True, center=True)
    p(doc, "ГАПОУ ИО «ИТК», 38.02.08 «Торговое дело», группа 69", 13, center=True)
    p(doc, "Два отдельных выступления, не парный доклад", 13, bold=True, center=True)
    p(doc, "«____» сентября 2026 г.", 13, center=True)
    h(doc, "Важно")
    p(doc, "Харитонов Н. В. и Карнаухова Т. П. выступают каждый со своей темой. Это не диалог и не смена голосов на одной сцене. У каждого свой текст, свои слайды, свои вопросы.")
    h(doc, "Доклад 1. Харитонов Никита Васильевич — тема 16")
    p(doc, "Для зала: «Иногда улица уже забита.»")
    p(doc, "Тезис. Даже верный расчёт чеков не спасает, если вошли последними в полный вагон.")
    p(doc, "Ось: вход последним на уже занятую улицу / в выдачу маркетплейса. Учебная модель 400 стаканов — не полевые данные Иркутска.")
    h(doc, "Доклад 2. Карнаухова Таисья Петровна — тема 18")
    p(doc, "Для зала: «Иногда человека съедает дом.»")
    p(doc, "Тезис. Дело иногда закрывают до удара рынка: у бизнеса обрезки времени, у дома — полный день.")
    p(doc, "Ось: семья и быт, вторая смена, закрытие ИП «чтобы сохранить мир». Не «девушки не созданы для бизнеса». Часы, не характер.")
    h(doc, "Общее для обоих")
    p(doc, "Закрытие ≠ провал. Цифра «80% в первый год» произносится как миф, не как факт.")
    p(doc, "Точка Банк / ТАСС, 26.05.2026: из открытых в 2022 к концу 2025 живы ≈ 50%.")
    p(doc, "У Таисьи дополнительно Росстат, бюджет времени 2019: женщины > 4 ч/сутки на дом и уход, мужчины < 2 ч. Год называют вслух.")
    h(doc, "Что не утверждаем")
    p(doc, "Что улица или семья — главная статистическая причина закрытий в РФ. Что 130-й квартал “убил N точек”. Что счёт 400 стаканов — полевые данные. Что женщины “не созданы для бизнеса”. Проценты CB Insights, SCORE, Вассермана.")
    h(doc, "Метод")
    p(doc, "Открытые источники + учебные сцены. Не полевое исследование группы. Темы 16 и 18 выбраны как человеческие оси для устного жанра.")
    add_sources_section(doc, SOURCES_NIKITA + [SOURCES_TAISIYA[-2], SOURCES_TAISIYA[-1]])
    path = OUT / "Для_преподавателя_два_доклада.docx"
    doc.save(path)
    return path


# ---------- PPTX helpers ----------
def set_run(run, size, bold=True, color=P_INK, name="Arial"):
    run.font.size = PPt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name
    run.font.italic = False


def add_text_box(slide, l, t, w, h, text, size=28, bold=True, color=P_INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    try:
        tf._txBody.bodyPr.set("anchor", {MSO_ANCHOR.TOP: "t", MSO_ANCHOR.MIDDLE: "ctr", MSO_ANCHOR.BOTTOM: "b"}.get(anchor, "t"))
    except Exception:
        pass
    pr = tf.paragraphs[0]
    pr.alignment = align
    run = pr.add_run()
    run.text = text
    set_run(run, size, bold, color)
    return box


def add_multiline(slide, l, t, w, h, lines, size=28, bold=True, color=P_INK, align=PP_ALIGN.LEFT, gap=8):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, text in enumerate(lines):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        para.space_after = PPt(gap)
        run = para.add_run()
        run.text = text
        set_run(run, size, bold, color)
    return box


def rect(slide, l, t, w, h, fill, line=None, line_w=Pt(2.25)):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = line_w
    sh.shadow.inherit = False
    return sh


def round_rect(slide, l, t, w, h, fill, line=P_DARK, line_w=Pt(2.5)):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = line
    sh.line.width = line_w
    sh.adjustments[0] = 0.12
    sh.shadow.inherit = False
    return sh


def shape_label(sh, text, size=16, color=P_INK):
    tf = sh.text_frame
    tf.word_wrap = True
    pr = tf.paragraphs[0]
    pr.alignment = PP_ALIGN.CENTER
    run = pr.add_run()
    run.text = text
    set_run(run, size, True, color)
    try:
        tf._txBody.bodyPr.set("anchor", "ctr")
    except Exception:
        pass


def footer(slide, n, total, who):
    add_text_box(slide, PInches(0.7), PInches(7.08), PInches(9.5), PInches(0.28),
                 f"ИТК  ·  группа 69  ·  {who}", 14, False, P_MUTED)
    add_text_box(slide, PInches(11.4), PInches(7.08), PInches(1.2), PInches(0.28),
                 f"{n}/{total}", 14, True, P_MUTED, PP_ALIGN.RIGHT)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def add_click_appears(slide, shape_ids_in_order):
    if not shape_ids_in_order:
        return
    sld = slide._element
    for old in sld.findall(pqn("p:timing")):
        sld.remove(old)
    child_tn = []
    for i, spid in enumerate(shape_ids_in_order):
        child_tn.append(f'''
          <p:par>
            <p:cTn id="{10+i}" fill="hold">
              <p:stCondLst>
                <p:cond delay="indefinite"/>
              </p:stCondLst>
              <p:childTnLst>
                <p:par>
                  <p:cTn id="{40+i}" fill="hold">
                    <p:stCondLst>
                      <p:cond delay="0"/>
                    </p:stCondLst>
                    <p:childTnLst>
                      <p:par>
                        <p:cTn id="{70+i}" presetID="1" presetClass="entr" presetSubtype="0" fill="hold" nodeType="clickEffect">
                          <p:stCondLst>
                            <p:cond delay="0"/>
                          </p:stCondLst>
                          <p:childTnLst>
                            <p:set>
                              <p:cBhvr>
                                <p:cTn id="{100+i}" dur="1" fill="hold"/>
                                <p:tgtEl>
                                  <p:spTgt spid="{spid}"/>
                                </p:tgtEl>
                                <p:attrNameLst>
                                  <p:attrName>style.visibility</p:attrName>
                                </p:attrNameLst>
                              </p:cBhvr>
                              <p:to>
                                <p:strVal val="visible"/>
                              </p:to>
                            </p:set>
                          </p:childTnLst>
                        </p:cTn>
                      </p:par>
                    </p:childTnLst>
                  </p:cTn>
                </p:par>
              </p:childTnLst>
            </p:cTn>
          </p:par>''')
    xml = f'''
    <p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
      <p:tnLst>
        <p:par>
          <p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
            <p:childTnLst>
              <p:seq concurrent="true" nextAc="seek">
                <p:cTn id="2" dur="indefinite" nodeType="mainSeq">
                  <p:childTnLst>
                    {''.join(child_tn)}
                  </p:childTnLst>
                </p:cTn>
                <p:prevCondLst>
                  <p:cond evt="onPrev" delay="0">
                    <p:tgtEl><p:sldTgt/></p:tgtEl>
                  </p:cond>
                </p:prevCondLst>
                <p:nextCondLst>
                  <p:cond evt="onNext" delay="0">
                    <p:tgtEl><p:sldTgt/></p:tgtEl>
                  </p:cond>
                </p:nextCondLst>
              </p:seq>
            </p:childTnLst>
          </p:cTn>
        </p:par>
      </p:tnLst>
    </p:timing>'''
    sld.append(etree.fromstring(xml))


def new_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = rect(slide, PInches(0), PInches(0), PInches(13.333), PInches(7.5), P_WHITE)
    spTree = slide.shapes._spTree
    sp = bg._element
    spTree.remove(sp)
    spTree.insert(2, sp)
    rect(slide, PInches(0), PInches(0), PInches(13.333), PInches(0.08), P_ACCENT)
    return slide


def new_prs():
    prs = Presentation()
    prs.slide_width = PInches(13.333)
    prs.slide_height = PInches(7.5)
    return prs


def slide_myth(prs, n, total, who):
    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Сначала ломаем страшилку", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.6), PInches(11.8), PInches(1.4), "80%", 96, True, P_ACCENT, PP_ALIGN.CENTER)
    rect(s, PInches(3.3), PInches(2.15), PInches(6.7), PInches(0.16), P_DARK)
    add_text_box(s, PInches(0.75), PInches(3.3), PInches(11.8), PInches(0.7),
                 "«закрываются в первый год»", 32, True, P_INK, PP_ALIGN.CENTER)
    pill = round_rect(s, PInches(4.7), PInches(4.4), PInches(3.9), PInches(0.85), P_DARK)
    shape_label(pill, "МИФ", 28, P_WHITE)
    add_text_box(s, PInches(0.75), PInches(5.55), PInches(11.8), PInches(0.5),
                 "Курсы повторяют. Когорты — нет.", 24, False, P_DARK, PP_ALIGN.CENTER)
    footer(s, n, total, who)
    return s


def slide_half(prs, n, total, who):
    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Что можно сказать вслух", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.2), PInches(11.8), PInches(1.1), "Примерно каждая вторая", 40, True, P_INK)
    add_text_box(s, PInches(0.75), PInches(2.35), PInches(11.8), PInches(0.7),
                 "из открытых в 2022-м ещё работала к концу 2025-го", 26, False, P_DARK)
    add_text_box(s, PInches(0.75), PInches(3.15), PInches(11.8), PInches(0.45),
                 "Точка Банк  ·  пересказ ТАСС  ·  26.05.2026", 20, True, P_ACCENT)
    labels = [("не начал", "не провал"), ("ушёл в найм", "не провал"), ("пустая фирма", "не провал")]
    for i, (a, b_) in enumerate(labels):
        x = PInches(0.75 + i * 4.05)
        round_rect(s, x, PInches(4.1), PInches(3.8), PInches(2.15), P_WHITE, P_DARK, Pt(3))
        add_text_box(s, x + PInches(0.2), PInches(4.3), PInches(3.4), PInches(0.8), a, 24, True, P_INK, PP_ALIGN.CENTER)
        add_text_box(s, x + PInches(0.2), PInches(5.15), PInches(3.4), PInches(0.7), b_, 22, True, P_ACCENT, PP_ALIGN.CENTER)
    footer(s, n, total, who)
    return s


def slide_sources(prs, n, total, who, cards):
    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Откуда цифры. Полный список — в Word.", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(0.85), PInches(11.8), PInches(0.55), "Можно открыть", 36, True, P_INK)
    for i, (a, b_) in enumerate(cards):
        col, row = i % 2, i // 2
        x = PInches(0.75 + col * 6.15)
        y = PInches(1.6 + row * 2.45)
        round_rect(s, x, y, PInches(5.85), PInches(2.2), P_WHITE, P_DARK, Pt(3))
        add_text_box(s, x + PInches(0.25), y + PInches(0.2), PInches(5.35), PInches(0.5), a, 20, True, P_ACCENT)
        add_text_box(s, x + PInches(0.25), y + PInches(0.75), PInches(5.35), PInches(1.2), b_, 26, True, P_INK)
    footer(s, n, total, who)
    notes(s, "СЛАЙД источников | не читать вслух, если не спросили.")
    return s


def slide_thanks(prs, n, total, fio, who):
    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(1.8), PInches(11.8), PInches(1.2), "Спасибо. Вопросы.", 48, True, P_INK, PP_ALIGN.CENTER)
    add_text_box(s, PInches(0.75), PInches(3.3), PInches(11.8), PInches(0.55), fio, 24, True, P_DARK, PP_ALIGN.CENTER)
    add_text_box(s, PInches(0.75), PInches(4.0), PInches(11.8), PInches(0.5),
                 "группа 69  ·  Торговое дело  ·  ГАПОУ ИО «ИТК»", 20, False, P_MUTED, PP_ALIGN.CENTER)
    footer(s, n, total, who)
    notes(s, "Спасибо. Вопросы. Шпаргалка ответов — в полном Word.")
    return s


def build_pptx_nikita():
    prs = new_prs()
    who = "Харитонов Н. В."
    total = 13
    speech = NIKITA_SPEECH

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.45), PInches(11.8), PInches(0.4),
                 "ГАПОУ ИО «ИТК»  ·  38.02.08 Торговое дело  ·  группа 69", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.5), PInches(11.8), PInches(1.3),
                 "Иногда улица уже забита.", 44, True, P_INK)
    add_text_box(s, PInches(0.75), PInches(3.0), PInches(11.8), PInches(0.9),
                 "Почему «открою такое же» — не стратегия", 26, False, P_DARK)
    plate = round_rect(s, PInches(0.75), PInches(4.7), PInches(7.4), PInches(1.55), P_WHITE, P_DARK, Pt(3))
    add_multiline(s, PInches(0.95), PInches(4.85), PInches(7.0), PInches(1.25),
                  ["Харитонов Никита Васильевич", "вошли последними"], 22, True, P_INK, gap=6)
    footer(s, 1, total, who)
    notes(s, "СЛАЙД 1 | 0:00\n" + "\n".join(speech[0][3]))

    s = slide_myth(prs, 2, total, who)
    notes(s, "СЛАЙД 2 | 0:30\n" + "\n".join(speech[1][3]))

    s = slide_half(prs, 3, total, who)
    notes(s, "СЛАЙД 3 | 1:00\n" + "\n".join(speech[2][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Тезис", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.5), PInches(11.8), PInches(2.4),
                 "Верный расчёт чеков\nне спасёт,\nесли вагон уже полный.", 36, True, P_INK)
    add_text_box(s, PInches(0.75), PInches(4.4), PInches(11.8), PInches(0.7),
                 "Один проход. Четыре одинаковых. Пятое «как у них».", 24, False, P_DARK)
    footer(s, 4, total, who)
    notes(s, "СЛАЙД 4 | 1:30\n" + "\n".join(speech[3][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.35), PInches(11.8), PInches(0.35), "Полный вагон", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(0.75), PInches(11.8), PInches(0.7), "Очередь соседа — не ваш спрос", 36, True, P_INK)
    add_text_box(s, PInches(0.75), PInches(1.5), PInches(11.8), PInches(0.45),
                 "Гостей уже разобрали. В его сторону.", 22, False, P_DARK)
    rect(s, PInches(0.75), PInches(5.85), PInches(11.8), PInches(0.18), P_DARK)
    for i in range(4):
        x = PInches(0.85 + i * 2.35)
        round_rect(s, x, PInches(3.15), PInches(2.15), PInches(2.45), P_WHITE, P_DARK, Pt(3))
        add_text_box(s, x, PInches(3.85), PInches(2.15), PInches(1.0), f"{i+1}", 40, True, P_INK, PP_ALIGN.CENTER)
    fifth = round_rect(s, PInches(10.25), PInches(3.15), PInches(2.15), PInches(2.45), P_ACCENT, P_DARK, Pt(3.5))
    add_text_box(s, PInches(10.25), PInches(3.85), PInches(2.15), PInches(1.1), "5", 44, True, P_WHITE, PP_ALIGN.CENTER)
    add_click_appears(s, [str(fifth._element.get("id"))])
    footer(s, 5, total, who)
    notes(s, "СЛАЙД 5 | 2:05 | КЛИК на 5-ю точку\n" + "\n".join(speech[4][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Почему сосед ещё жив", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(0.95), PInches(11.8), PInches(1.1), "Копируют витрину.\nНе экономику.", 40, True, P_INK)
    items = [("старая аренда", "не ваша цена метра"), ("свои люди", "ходят третий год"), ("свой поставщик", "вам он чужой")]
    for i, (a, b_) in enumerate(items):
        x = PInches(0.75 + i * 4.05)
        round_rect(s, x, PInches(3.5), PInches(3.85), PInches(2.55), P_WHITE, P_DARK, Pt(3))
        add_text_box(s, x + PInches(0.2), PInches(3.75), PInches(3.45), PInches(1.0), a, 26, True, P_INK, PP_ALIGN.CENTER)
        add_text_box(s, x + PInches(0.2), PInches(4.85), PInches(3.45), PInches(0.8), b_, 20, False, P_DARK, PP_ALIGN.CENTER)
    footer(s, 6, total, who)
    notes(s, "СЛАЙД 6 | 2:40\n" + "\n".join(speech[5][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Та же улица — в телефоне", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(0.95), PInches(11.8), PInches(0.8), "Последние в выдаче", 40, True, P_INK)
    for r in range(2):
        for c in range(6):
            x = PInches(0.75 + c * 2.05)
            y = PInches(2.15 + r * 1.55)
            is_last = r == 1 and c == 5
            round_rect(s, x, y, PInches(1.9), PInches(1.4),
                       P_ACCENT if is_last else P_WHITE, P_DARK, Pt(2.75))
            add_text_box(s, x, y + PInches(0.4), PInches(1.9), PInches(0.6),
                         "ВЫ" if is_last else "то же", 18, True, P_WHITE if is_last else P_INK, PP_ALIGN.CENTER)
    add_text_box(s, PInches(0.75), PInches(5.45), PInches(11.8), PInches(0.7),
                 "Цена  ·  отзывы  ·  кто выше  ·  аренда спрятана", 24, True, P_DARK, PP_ALIGN.CENTER)
    footer(s, 7, total, who)
    notes(s, "СЛАЙД 7 | 3:20\n" + "\n".join(speech[6][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.35), PInches(11.8), PInches(0.35), "Условный счёт. Не статистика Иркутска.", 18, True, P_ACCENT)
    add_text_box(s, PInches(0.75), PInches(0.85), PInches(11.8), PInches(0.7), "400 стаканов на проходе", 36, True, P_INK)
    round_rect(s, PInches(0.75), PInches(1.85), PInches(5.7), PInches(4.4), P_WHITE, P_DARK, Pt(3))
    add_text_box(s, PInches(0.95), PInches(2.05), PInches(5.3), PInches(0.5), "4 точки", 24, True, P_MUTED)
    add_text_box(s, PInches(0.95), PInches(2.7), PInches(5.3), PInches(1.3), "по 100", 60, True, P_INK, PP_ALIGN.CENTER)
    add_text_box(s, PInches(0.95), PInches(4.3), PInches(5.3), PInches(1.2), "порог новой ≈ 90", 24, False, P_DARK, PP_ALIGN.CENTER)
    round_rect(s, PInches(6.85), PInches(1.85), PInches(5.7), PInches(4.4), P_WHITE, P_ACCENT, Pt(3.5))
    add_text_box(s, PInches(7.05), PInches(2.05), PInches(5.3), PInches(0.5), "5 точек", 24, True, P_MUTED)
    add_text_box(s, PInches(7.05), PInches(2.7), PInches(5.3), PInches(1.3), "по 80", 60, True, P_ACCENT, PP_ALIGN.CENTER)
    add_text_box(s, PInches(7.05), PInches(4.3), PInches(5.3), PInches(1.2), "ниже порога", 24, True, P_DARK, PP_ALIGN.CENTER)
    footer(s, 8, total, who)
    notes(s, "СЛАЙД 8 | 4:10 и вывод 4:50\n" + "\n".join(speech[7][3] + speech[8][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "До вывески. Три вопроса.", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(0.9), PInches(11.8), PInches(0.7), "Не «как красиво у них»", 36, True, P_INK)
    qs = [
        ("1", "Сколько гостей ещё не разобрано?"),
        ("2", "Какая аренда против его старой?"),
        ("3", "Чем я не копия?"),
    ]
    for i, (num, text) in enumerate(qs):
        y = PInches(1.85 + i * 1.55)
        round_rect(s, PInches(0.75), y, PInches(11.8), PInches(1.4), P_WHITE, P_DARK, Pt(3))
        add_text_box(s, PInches(1.0), y + PInches(0.3), PInches(1.0), PInches(0.8), num, 36, True, P_ACCENT)
        add_text_box(s, PInches(2.2), y + PInches(0.4), PInches(10.0), PInches(0.7), text, 26, True, P_INK)
    footer(s, 9, total, who)
    notes(s, "СЛАЙД 9 | 5:15\n" + "\n".join(speech[9][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Через год в реестре", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.4), PInches(11.8), PInches(1.8),
                 "«Не пошло».\nНа самом деле — разрезали чужой поток.", 36, True, P_INK)
    add_text_box(s, PInches(0.75), PInches(3.7), PInches(11.8), PInches(1.2),
                 "Страшилка «80%» прячет конкретную ошибку.", 26, False, P_DARK)
    footer(s, 10, total, who)
    notes(s, "СЛАЙД 10 | 6:00\n" + "\n".join(speech[10][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Что забрать. Один вопрос.", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.5), PInches(11.8), PInches(2.4),
                 "Сколько гостей на проходе\nещё не разобрано?", 40, True, P_INK)
    add_text_box(s, PInches(0.75), PInches(4.3), PInches(11.8), PInches(1.0),
                 "«У них очередь» — это надежда. Надежда не платит аренду.", 24, False, P_DARK)
    footer(s, 11, total, who)
    notes(s, "СЛАЙД 11 | 6:40\n" + "\n".join(speech[11][3]))

    slide_sources(prs, 12, total, who, [
        ("Точка / ТАСС", "≈ 50% когорты 2022\nк концу 2025"),
        ("BLS, Table 7", "первый год в США\n≈ каждый пятый"),
        ("ФНС / аудит", "чистка юрлиц\n≠ смерть кафе"),
        ("учебная модель", "400 стаканов\nне поле Иркутска"),
    ])

    slide_thanks(prs, 13, total, "Харитонов Никита Васильевич", who)

    path = OUT / "НИКИТА_презентация.pptx"
    prs.save(path)
    return path


def build_pptx_taisiya():
    prs = new_prs()
    who = "Карнаухова Т. П."
    total = 13
    speech = TAISIYA_SPEECH

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.45), PInches(11.8), PInches(0.4),
                 "ГАПОУ ИО «ИТК»  ·  38.02.08 Торговое дело  ·  группа 69", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.5), PInches(11.8), PInches(1.3),
                 "Иногда человека съедает дом.", 40, True, P_INK)
    add_text_box(s, PInches(0.75), PInches(3.0), PInches(11.8), PInches(0.9),
                 "Почему дело закрывают до удара рынка", 26, False, P_DARK)
    round_rect(s, PInches(0.75), PInches(4.7), PInches(7.8), PInches(1.55), P_WHITE, P_ACCENT, Pt(3))
    add_multiline(s, PInches(0.95), PInches(4.85), PInches(7.4), PInches(1.25),
                  ["Карнаухова Таисья Петровна", "часы, не характер"], 22, True, P_INK, gap=6)
    footer(s, 1, total, who)
    notes(s, "СЛАЙД 1 | 0:00\n" + "\n".join(speech[0][3]))

    s = slide_myth(prs, 2, total, who)
    notes(s, "СЛАЙД 2 | 0:30\n" + "\n".join(speech[1][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "В одной графе «закрылись»", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.1), PInches(11.8), PInches(0.8), "Не всегда «прогореть»", 36, True, P_INK)
    labels = [
        ("не начал", "не провал"),
        ("ушёл в найм", "не провал"),
        ("закрыл, чтобы\nсохранить мир", "моя тема"),
    ]
    for i, (a, b_) in enumerate(labels):
        x = PInches(0.75 + i * 4.05)
        border = P_ACCENT if i == 2 else P_DARK
        round_rect(s, x, PInches(2.4), PInches(3.85), PInches(3.5), P_WHITE, border, Pt(3.5 if i == 2 else 3))
        add_text_box(s, x + PInches(0.15), PInches(2.7), PInches(3.55), PInches(1.6), a, 24, True, P_INK, PP_ALIGN.CENTER)
        add_text_box(s, x + PInches(0.15), PInches(4.5), PInches(3.55), PInches(0.8), b_, 22, True, P_ACCENT, PP_ALIGN.CENTER)
    footer(s, 3, total, who)
    notes(s, "СЛАЙД 3 | 0:55\n" + "\n".join(speech[2][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Тезис", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.4), PInches(11.8), PInches(2.6),
                 "У бизнеса — обрезки часов.\nУ дома — полный день.", 40, True, P_INK)
    add_text_box(s, PInches(0.75), PInches(4.4), PInches(11.8), PInches(0.8),
                 "Спрос может быть. Не хватает суток.", 24, False, P_DARK)
    footer(s, 4, total, who)
    notes(s, "СЛАЙД 4 | 1:30\n" + "\n".join(speech[3][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Один вечер и тридцать вечеров", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.1), PInches(11.8), PInches(1.6), "Клиент подождёт.\nДом — нет.", 44, True, P_INK)
    round_rect(s, PInches(0.75), PInches(3.3), PInches(5.6), PInches(2.7), P_WHITE, P_DARK, Pt(3))
    round_rect(s, PInches(6.95), PInches(3.3), PInches(5.6), PInches(2.7), P_WHITE, P_ACCENT, Pt(3.5))
    add_text_box(s, PInches(0.95), PInches(3.7), PInches(5.2), PInches(1.8), "телефон\nзаказ, ответ, выйти", 26, True, P_INK, PP_ALIGN.CENTER)
    add_text_box(s, PInches(7.15), PInches(3.7), PInches(5.2), PInches(1.8), "комната\nмагазин, ребёнок, «ты же дома»", 24, True, P_INK, PP_ALIGN.CENTER)
    footer(s, 5, total, who)
    notes(s, "СЛАЙД 5 | 1:55\n" + "\n".join(speech[4][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.35), PInches(11.8), PInches(0.35), "Не характер. Часы. Росстат, 2019.", 18, True, P_ACCENT)
    add_text_box(s, PInches(0.75), PInches(0.8), PInches(11.8), PInches(0.7), "Вторая смена без зарплаты", 36, True, P_INK)
    round_rect(s, PInches(0.75), PInches(1.8), PInches(5.7), PInches(2.5), P_WHITE, P_DARK, Pt(3))
    add_text_box(s, PInches(0.95), PInches(1.95), PInches(5.3), PInches(0.45), "дом и уход, женщины", 18, False, P_MUTED)
    add_text_box(s, PInches(0.95), PInches(2.4), PInches(5.3), PInches(1.2), "> 4 часов", 44, True, P_INK, PP_ALIGN.CENTER)
    round_rect(s, PInches(6.85), PInches(1.8), PInches(5.7), PInches(2.5), P_WHITE, P_DARK, Pt(3))
    add_text_box(s, PInches(7.05), PInches(1.95), PInches(5.3), PInches(0.45), "дом и уход, мужчины", 18, False, P_MUTED)
    add_text_box(s, PInches(7.05), PInches(2.4), PInches(5.3), PInches(1.2), "< 2 часов", 44, True, P_INK, PP_ALIGN.CENTER)
    add_text_box(s, PInches(0.75), PInches(4.6), PInches(11.8), PInches(1.4),
                 "Тема не про «девушек».\nПро любого, на ком висит дом.", 26, True, P_DARK)
    footer(s, 6, total, who)
    notes(s, "СЛАЙД 6 | 2:40\n" + "\n".join(speech[5][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Сутки не резиновые", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(0.9), PInches(11.8), PInches(0.8), "На дело остаются обрезки", 36, True, P_INK)
    rect(s, PInches(0.75), PInches(2.4), PInches(3.3), PInches(2.2), P_DARK)
    add_text_box(s, PInches(0.75), PInches(3.15), PInches(3.3), PInches(0.7), "сон", 24, True, P_WHITE, PP_ALIGN.CENTER)
    rect(s, PInches(4.05), PInches(2.4), PInches(3.6), PInches(2.2), P_MUTED)
    add_text_box(s, PInches(4.05), PInches(3.15), PInches(3.6), PInches(0.7), "учёба / смена", 24, True, P_WHITE, PP_ALIGN.CENTER)
    rect(s, PInches(7.65), PInches(2.4), PInches(2.7), PInches(2.2), P_ACCENT)
    add_text_box(s, PInches(7.65), PInches(3.15), PInches(2.7), PInches(0.7), "дом", 24, True, P_WHITE, PP_ALIGN.CENTER)
    rect(s, PInches(10.35), PInches(2.4), PInches(2.2), PInches(2.2), P_WHITE, P_DARK, Pt(3))
    add_text_box(s, PInches(10.35), PInches(3.15), PInches(2.2), PInches(0.7), "дело?", 24, True, P_INK, PP_ALIGN.CENTER)
    add_text_box(s, PInches(0.75), PInches(5.0), PInches(11.8), PInches(1.0),
                 "Пол не при чём. Часы при чём.", 28, True, P_DARK)
    footer(s, 7, total, who)
    notes(s, "СЛАЙД 7 | 3:25\n" + "\n".join(speech[6][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Почему это про торговлю", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.3), PInches(11.8), PInches(2.0),
                 "Карточка без ответа\n— мёртвая карточка.", 40, True, P_INK)
    add_text_box(s, PInches(0.75), PInches(3.7), PInches(11.8), PInches(1.4),
                 "Покупатель не знает про вашу семью.\nОн знает, что ему не ответили.", 26, False, P_DARK)
    footer(s, 8, total, who)
    notes(s, "СЛАЙД 8 | 4:00\n" + "\n".join(speech[7][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "В реестре это выглядит как провал", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.15), PInches(11.8), PInches(1.5), "Рынок ещё не начал\nубивать.", 40, True, P_INK)
    add_text_box(s, PInches(0.75), PInches(3.0), PInches(11.8), PInches(0.6), "Закрыли ИП, чтобы сохранить мир.", 26, True, P_DARK)
    items = ["меньше ссор", "меньше риска", "строка в ЕГРИП"]
    for i, t in enumerate(items):
        x = PInches(0.75 + i * 4.05)
        round_rect(s, x, PInches(4.0), PInches(3.85), PInches(2.05), P_WHITE, P_DARK, Pt(3))
        add_text_box(s, x + PInches(0.15), PInches(4.55), PInches(3.55), PInches(1.0), t, 24, True, P_INK, PP_ALIGN.CENTER)
    footer(s, 9, total, who)
    notes(s, "СЛАЙД 9 | 4:40\n" + "\n".join(speech[8][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Два честных желания", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.2), PInches(11.8), PInches(1.2), "Выбор есть.\nБесплатного выбора нет.", 40, True, P_INK)
    round_rect(s, PInches(0.75), PInches(3.1), PInches(5.6), PInches(2.8), P_WHITE, P_DARK, Pt(3))
    round_rect(s, PInches(6.95), PInches(3.1), PInches(5.6), PInches(2.8), P_WHITE, P_ACCENT, Pt(3.5))
    add_text_box(s, PInches(0.95), PInches(3.5), PInches(5.2), PInches(2.0), "жёсткость без\nдоговорённости\nломает дом", 24, True, P_INK, PP_ALIGN.CENTER)
    add_text_box(s, PInches(7.15), PInches(3.5), PInches(5.2), PInches(2.0), "мягкость без\nграниц\nломает дело", 24, True, P_INK, PP_ALIGN.CENTER)
    footer(s, 10, total, who)
    notes(s, "СЛАЙД 10 | 5:20 и 5:50\n" + "\n".join(speech[9][3] + speech[10][3]))

    s = new_slide(prs)
    add_text_box(s, PInches(0.75), PInches(0.4), PInches(11.8), PInches(0.4), "Что забрать. Один разговор до открытия.", 18, False, P_MUTED)
    add_text_box(s, PInches(0.75), PInches(1.4), PInches(11.8), PInches(2.2),
                 "У кого в семье\nкакие часы?", 44, True, P_INK)
    add_text_box(s, PInches(0.75), PInches(4.0), PInches(11.8), PInches(1.4),
                 "Не «поддержишь меня?».\nКто отвечает после десяти. Кто забирает ребёнка в среду.", 24, False, P_DARK)
    footer(s, 11, total, who)
    notes(s, "СЛАЙД 11 | 6:25 и 7:05\n" + "\n".join(speech[11][3] + speech[12][3]))

    slide_sources(prs, 12, total, who, [
        ("Точка / ТАСС", "≈ 50% когорты 2022\nк концу 2025"),
        ("Росстат, 2019", "дом и уход\n>4 ч и <2 ч"),
        ("вторая смена", "механизм часов\nне доля закрытий"),
        ("ФНС / аудит", "чистка юрлиц\n≠ смерть кафе"),
    ])

    slide_thanks(prs, 13, total, "Карнаухова Таисья Петровна", who)

    path = OUT / "ТАИСЬЯ_презентация.pptx"
    prs.save(path)
    return path


def nikita_section(slide, paras):
    if slide <= 3:
        return "1. Крючок и миф про 80%"
    if slide <= 8:
        return "2. Забитая улица"
    if slide == 9:
        return "3. Три вопроса до вывески"
    if slide in (10, 11):
        return "4. Финал"
    if slide >= 13:
        return "5. Вопросы"
    return None


def taisiya_section(slide, paras):
    if slide <= 3:
        return "1. Крючок и миф про 80%"
    if slide <= 7:
        return "2. Дом и часы"
    if slide <= 10:
        return "3. Торговля и выбор"
    if slide == 11:
        return "4. Финал"
    if slide >= 13:
        return "5. Вопросы"
    return None


NIKITA = {
    "who": "НИКИТА",
    "fio": "Харитонов Никита Васильевич",
    "title1": "Почему бизнесы закрываются в первый год —",
    "title2": "и почему «открою такое же» не стратегия",
    "hall": "Для зала: Иногда улица уже забита.",
    "header_full": "Харитонов Н. В.  ·  группа 69  ·  ИТК  ·  полный текст  ·  отдельный доклад",
    "header_cards": "Харитонов Н. В.  ·  карточки  ·  группа 69  ·  ИТК",
    "full_name": "НИКИТА_полный_текст.docx",
    "cards_name": "НИКИТА_карточки.docx",
    "speech": NIKITA_SPEECH,
    "qa": NIKITA_QA,
    "sources": SOURCES_NIKITA,
    "toc": [
        "1. Крючок и миф про 80%",
        "2. Забитая улица (тема 16)",
        "3. Три вопроса до вывески",
        "4. Финал",
        "5. Вопросы преподавателю — шпаргалка",
        "6. Источники",
    ],
    "section_for": nikita_section,
}

TAISIYA = {
    "who": "ТАИСЬЯ",
    "fio": "Карнаухова Таисья Петровна",
    "title1": "Почему бизнесы закрываются в первый год —",
    "title2": "и почему человека иногда съедает дом",
    "hall": "Для зала: Иногда человека съедает дом.",
    "header_full": "Карнаухова Т. П.  ·  группа 69  ·  ИТК  ·  полный текст  ·  отдельный доклад",
    "header_cards": "Карнаухова Т. П.  ·  карточки  ·  группа 69  ·  ИТК",
    "full_name": "ТАИСЬЯ_полный_текст.docx",
    "cards_name": "ТАИСЬЯ_карточки.docx",
    "speech": TAISIYA_SPEECH,
    "qa": TAISIYA_QA,
    "sources": SOURCES_TAISIYA,
    "toc": [
        "1. Крючок и миф про 80%",
        "2. Дом и часы (тема 18)",
        "3. Торговля и выбор",
        "4. Финал",
        "5. Вопросы преподавателю — шпаргалка",
        "6. Источники",
    ],
    "section_for": taisiya_section,
}


OLD_NAMES = [
    "ВЫСТУПЛЕНИЕ_полный_текст_на_двоих.docx",
    "ВЫСТУПЛЕНИЕ_карточки_Никита.docx",
    "ВЫСТУПЛЕНИЕ_карточки_Таисья.docx",
    "Для_преподавателя_кратко.docx",
    "ПРЕЗЕНТАЦИЯ_улица_и_дом.pptx",
    "ПРЕЗЕНТАЦИЯ_улица_и_дом.pdf",
]


def pack_downloads(files):
    if DL.exists():
        shutil.rmtree(DL)
    DL.mkdir(parents=True)

    mapping = {
        "НИКИТА_полный_текст.docx": "nikita-polnyy-tekst.docx",
        "НИКИТА_полный_текст.pdf": "nikita-polnyy-tekst.pdf",
        "НИКИТА_карточки.docx": "nikita-kartochki.docx",
        "НИКИТА_презентация.pptx": "nikita-prezentaciya.pptx",
        "НИКИТА_презентация.pdf": "nikita-prezentaciya.pdf",
        "ТАИСЬЯ_полный_текст.docx": "taisiya-polnyy-tekst.docx",
        "ТАИСЬЯ_полный_текст.pdf": "taisiya-polnyy-tekst.pdf",
        "ТАИСЬЯ_карточки.docx": "taisiya-kartochki.docx",
        "ТАИСЬЯ_презентация.pptx": "taisiya-prezentaciya.pptx",
        "ТАИСЬЯ_презентация.pdf": "taisiya-prezentaciya.pdf",
        "Для_преподавателя_два_доклада.docx": "dlya-prepodavatelya.docx",
    }
    ascii_paths = []
    for src in files:
        name = mapping.get(src.name)
        if not name:
            continue
        dst = DL / name
        shutil.copy2(src, dst)
        ascii_paths.append(dst)

    def zip_paths(zip_name, paths):
        zpath = DL / zip_name
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
            for pth in paths:
                zf.write(pth, pth.name)
        return zpath

    nikita = [p for p in ascii_paths if p.name.startswith("nikita-")]
    taisiya = [p for p in ascii_paths if p.name.startswith("taisiya-")]
    teacher = [p for p in ascii_paths if p.name.startswith("dlya-")]
    zip_paths("nikita.zip", nikita)
    zip_paths("taisiya.zip", taisiya)
    zip_paths("vystuplenie-itk-vse.zip", ascii_paths)

    for pth in DL.iterdir():
        shutil.copy2(pth, ART / pth.name)
    for src in files:
        shutil.copy2(src, ART / src.name)


def main():
    print("NIKITA_WORDS", word_count(NIKITA_SPEECH))
    print("TAISIYA_WORDS", word_count(TAISIYA_SPEECH))
    files = []
    files.append(build_full(NIKITA))
    files.append(build_cards(NIKITA))
    files.append(build_full(TAISIYA))
    files.append(build_cards(TAISIYA))
    files.append(build_teacher())
    files.append(build_pptx_nikita())
    files.append(build_pptx_taisiya())
    files.append(build_full_pdf(NIKITA))
    files.append(build_full_pdf(TAISIYA))

    def to_pdf(src: Path) -> Path:
        safe = {
            "НИКИТА_презентация.pptx": "nikita-prezentaciya.pptx",
            "ТАИСЬЯ_презентация.pptx": "taisiya-prezentaciya.pptx",
        }[src.name]
        tmp = Path("/tmp") / safe
        shutil.copy2(src, tmp)
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", "/tmp", str(tmp)],
            check=True,
        )
        pdf_tmp = tmp.with_suffix(".pdf")
        pdf_out = src.with_suffix(".pdf")
        shutil.copy2(pdf_tmp, pdf_out)
        return pdf_out

    for src in (OUT / "НИКИТА_презентация.pptx", OUT / "ТАИСЬЯ_презентация.pptx"):
        files.append(to_pdf(src))
    for old in OLD_NAMES:
        for folder in (OUT, ART):
            pth = folder / old
            if pth.exists():
                pth.unlink()
    pack_downloads(files)
    for f in files:
        print("WROTE", f)


if __name__ == "__main__":
    main()
