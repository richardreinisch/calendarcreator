
import locale
import calendar
import csv
from datetime import date, timedelta
from collections.abc import Iterable
import pymupdf


YEAR = 2026
FONT_FILE = "font/Silkscreen-Regular.ttf"
FONT_NAME = "F1"
LOGO_FILE = "logo/logo.png"
TEMPLATE_FILE = "template/Template.pdf"
SPECIAL_DATES_FILE = "data/special-dates.csv"
COLUMN_WIDTH_MM = 27
MM_TO_PT_FACTOR = 2.83465


def get_styrian_holidays(year: int) -> dict[str, str]:

    holidays = {
        f"{year}-01-01": "Neujahr",
        f"{year}-01-06": "Heilige Drei Könige",
        f"{year}-05-01": "Staatsfeiertag",
        f"{year}-08-15": "Mariä Himmelfahrt",
        f"{year}-10-26": "Nationalfeiertag",
        f"{year}-11-01": "Allerheiligen",
        f"{year}-12-08": "Mariä Empfängnis",
        f"{year}-12-24": "Heiliger Abend",
        f"{year}-12-25": "Christtag",
        f"{year}-12-26": "Stefanitag",
        f"{year}-12-31": "Sylvester"
    }

    easter = easter_sunday(year)
    holidays[easter.strftime("%Y-%m-%d")] = "Ostersonntag"
    holidays[(easter + timedelta(days=1)).strftime("%Y-%m-%d")] = "Ostermontag"
    holidays[(easter + timedelta(days=39)).strftime("%Y-%m-%d")] = "Christi Himmelfahrt"
    holidays[(easter + timedelta(days=49)).strftime("%Y-%m-%d")] = "Pfingstsonntag"
    holidays[(easter + timedelta(days=50)).strftime("%Y-%m-%d")] = "Pfingstmontag"
    holidays[(easter + timedelta(days=60)).strftime("%Y-%m-%d")] = "Fronleichnam"

    return holidays


def easter_sunday(year: int) -> date:

    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)

def mm_to_points(mm: float) -> float:

    return mm * MM_TO_PT_FACTOR


def all_days_in_year(year: int) -> Iterable[date]:

    start = date(year, 1, 1)
    end = date(year, 12, 31)
    delta = timedelta(days=1)
    current = start
    while current <= end:
        yield current
        current += delta


def create_front_page(page: pymupdf.Page) -> None:
    try:
        page.insert_image(
            pymupdf.Rect(
                mm_to_points(84), mm_to_points(45),
                mm_to_points(84 + 40), mm_to_points(45 + 40)
            ),
            filename=LOGO_FILE
        )
    except FileNotFoundError:
        print("Could not find Logo file.")

    page.insert_text(
        (mm_to_points(85), mm_to_points(95)),
        "MEIN KALENDER",
        fontsize=12,
        fontname=FONT_NAME,
        fontfile=FONT_FILE
    )
    page.insert_text(
        (mm_to_points(85), mm_to_points(105)),
        str(YEAR),
        fontsize=37,
        fontname=FONT_NAME,
        fontfile=FONT_FILE
    )


def create_header(page: pymupdf.Page, month_name: str, year: int, week: int) -> None:

    page.insert_text(
        (mm_to_points(10), mm_to_points(20)),
        month_name,
        fontsize=13,
        fontname=FONT_NAME,
        fontfile=FONT_FILE
    )
    page.insert_text(
        (mm_to_points(10 + 6 * COLUMN_WIDTH_MM), mm_to_points(20)),
        f"{year} KW{week:02}",
        fontsize=13,
        fontname=FONT_NAME,
        fontfile=FONT_FILE
    )


def create_additional_header(page: pymupdf.Page, day: date, month_name: str) -> None:

    page.insert_text(
        (mm_to_points(10) + mm_to_points(day.weekday() * COLUMN_WIDTH_MM), mm_to_points(20)),
        month_name,
        fontsize=13,
        fontname=FONT_NAME,
        fontfile=FONT_FILE
    )


def create_day_column(page: pymupdf.Page, day: date, day_name: str, special: dict[str, str]) -> None:

    page.insert_text(
        (mm_to_points(10) + mm_to_points(day.weekday() * COLUMN_WIDTH_MM), mm_to_points(30)),
        str(day.day).zfill(2) + ".",
        fontsize=13,
        fontname=FONT_NAME,
        fontfile=FONT_FILE
    )
    page.insert_text(
        (mm_to_points(20) + mm_to_points(day.weekday() * COLUMN_WIDTH_MM), mm_to_points(30)),
        day_name,
        fontsize=7,
        fontname=FONT_NAME,
        fontfile=FONT_FILE
    )

    if str(day) in STYRIAN_HOLIDAYS:
        page.insert_text(
            (mm_to_points(10) + mm_to_points(day.weekday() * COLUMN_WIDTH_MM), mm_to_points(35)),
            STYRIAN_HOLIDAYS[str(day)],
            fontsize=5,
            fontname=FONT_NAME,
            fontfile=FONT_FILE
        )

    simple_date = f"{day.month:02}-{day.day:02}"

    if simple_date in special:
        entries = special[simple_date].split(":")
        for i, entry in enumerate(entries):
            page.insert_text(
                (mm_to_points(13) + mm_to_points(day.weekday() * COLUMN_WIDTH_MM), mm_to_points(45 + 7 * i)),
                entry[:12],
                fontsize=7,
                fontname=FONT_NAME,
                fontfile=FONT_FILE
            )


def create_new_page_using_template(doc: pymupdf.Document,
                                   template_document: pymupdf.Document,
                                   template_size_definition: pymupdf.Rect) -> pymupdf.Page:

    page = doc.new_page(width=template_size_definition.width, height=template_size_definition.height)
    page.show_pdf_page(template_size_definition, template_document, 0)
    return page


def read_special_dates_csv() -> None:

    try:
        with open(SPECIAL_DATES_FILE, 'r', encoding='utf8') as file:
            reader = csv.reader(file, delimiter=',')
            for row in reader:
                special_dates[row[0]] = row[1]
    except FileNotFoundError:
        print("special-dates.csv not found.")
    except IOError:
        print("Error during reading special-dates.csv.")



if __name__ == "__main__":

    locale.setlocale(locale.LC_ALL, 'de_AT.UTF-8')
    STYRIAN_HOLIDAYS = get_styrian_holidays(YEAR)
    special_dates = { }
    template = pymupdf.open(TEMPLATE_FILE)
    final_document_A5 = pymupdf.open()
    template_page = template[0]
    size_definition_A5 = template_page.rect
    font = pymupdf.Font()
    read_special_dates_csv()
    page_index = 1
    previous_weekday = 0

    new_page = final_document_A5.new_page(width=size_definition_A5.width, height=size_definition_A5.height)
    create_front_page(new_page)

    new_page = create_new_page_using_template(final_document_A5, template, size_definition_A5)
    create_header(new_page, calendar.month_name[1], YEAR, page_index)

    for selected_day in all_days_in_year(YEAR):

        if previous_weekday == 6 and selected_day.weekday() == 0:
            new_page = create_new_page_using_template(final_document_A5, template, size_definition_A5)
            create_header(new_page, calendar.month_name[selected_day.month], YEAR, page_index + 1)
            page_index += 1

        if selected_day.day == 1 and page_index > 1 and 1 < selected_day.weekday() < 6:
            create_additional_header(new_page, selected_day, calendar.month_name[selected_day.month])

        create_day_column(new_page, selected_day, calendar.day_name[selected_day.weekday()][:2], special_dates)

        previous_weekday = selected_day.weekday()

    filepath = "output/Mein_Kalender_A5_" + str(YEAR) + ".pdf"

    final_document_A5.save(filepath)
    print("Successfully Created A5 Document " + filepath)

    template.close()

    final_document_A4 = pymupdf.open()
    size_definition_A4 = pymupdf.Rect(0, 0, size_definition_A5.width, size_definition_A5.height * 2)

    for i in range(0, len(final_document_A5), 2):

        page = final_document_A4.new_page(width=size_definition_A4.width, height=size_definition_A4.height)
        top_rectangle = pymupdf.Rect(0, 0, size_definition_A4.width, size_definition_A4.height / 2)

        if i < len(final_document_A5):
            page.show_pdf_page(top_rectangle, final_document_A5, i)

        bottom_rectangle = pymupdf.Rect(0, size_definition_A4.height / 2, size_definition_A4.width, size_definition_A4.height)

        if i + 1 < len(final_document_A5):
            page.show_pdf_page(bottom_rectangle, final_document_A5, i + 1)

    filepath = "output/Mein_Kalender_A4_" + str(YEAR) + ".pdf"
    final_document_A4.save(filepath)

    print("Successfully Created A4 Document " + filepath)

    final_document_A5.close()
    final_document_A4.close()
