from app.services.document_extractor import clean_text


def test_clean_text_normalizes_spaces_and_page_footer():
    text = "Dr. Jane   Doe\r\n\n\nPage 1 of 2\nMBBS\tCardiology"
    assert clean_text(text) == "Dr. Jane Doe\n\n MBBS Cardiology"
