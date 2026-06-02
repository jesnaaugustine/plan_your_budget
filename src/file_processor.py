from PyPDF2 import PageObject, PdfReader
import logging
import pytesseract
from PIL import Image
import cv2
import io   


from src.utils import setup_logging,clean_text

setup_logging()
logger = logging.getLogger(__name__)
def process_file(file_path):
    file_type =file_path.split('.')[-1]
    if file_type.lower()=='pdf':
        cleaned_data=process_pdf(file_path)
    elif file_type.lower()=='png' or file_type.lower()=='jpg' or file_type.lower()=='jpeg' :
        cleaned_data =process_image(file_path)
    elif file_type.lower()=='txt':
        cleaned_data =process_txt(file_path)
    return cleaned_data

    #logger.info(f'extracted content {cleaned_data}')




def process_pdf(file):
    text = ""
    with open(file, "rb") as f:
        pdf_reader = PdfReader(f)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                    logger.info(f"Extracted text from page {page_num} without OCR.")
                else:
                    logger.info(f"No text found on page {page_num}; attempting OCR.")
                    text += extract_text_from_images(page)
            except Exception as e:
                logger.error(f"Error processing page {page_num}: {e}")
    cleaned_data = clean_text(text)
    logger.info(f"Completed text extraction for {file}")
    return cleaned_data


def process_txt(file):
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()
        logger.info(text)
        entries = [ text.strip() for text in text.split("---end_of_text---") if text.strip()]

        last_entry = entries[-1]
        logger.info(last_entry)
    return clean_text(last_entry)

def extract_text_from_images(page: PageObject) -> str:
    """
    Extracts text from images on a page using OCR.

    Args:
        page (PageObject): The PDF page object containing images.

    Returns:
        str: Extracted text from images using OCR.
    """
    text = ""
    for image_file_object in page.images:
        try:
            image = Image.open(io.BytesIO(image_file_object.data))
            ocr_text = pytesseract.image_to_string(image)
            text += ocr_text
            logger.info("Extracted text from image using OCR.")
        except Exception as e:
            logger.error(f"Error processing image for OCR: {e}")
    return text

def process_image(file):
    image = cv2.imread(file)

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    _, thresh = cv2.threshold(gray, 150,255,cv2.THRESH_BINARY)

    text = pytesseract.image_to_string(
        thresh,
        config='--oem 3 --psm 6'
    )
    cleaned_data = clean_text(text)
    logger.info(f"Completed text extraction for {file}")
    return cleaned_data
