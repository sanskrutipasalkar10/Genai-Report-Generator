import fitz  # PyMuPDF
from docx import Document
import io
import base64
import os
import logging

logger = logging.getLogger(__name__)

def extract_images_from_file(file_path: str) -> list:
    """
    Extracts images from PDF or DOCX and returns them as Base64 strings.
    Returns: List[str] (list of base64 strings)
    """
    images_base64 = []
    
    try:
        # 1. PDF Image Extraction
        if file_path.lower().endswith('.pdf'):
            try:
                doc = fitz.open(file_path)
                for page_index in range(len(doc)):
                    page = doc[page_index]
                    image_list = page.get_images(full=True)
                    
                    for img_index, img in enumerate(image_list):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Filter small icons/logos (size check)
                        if len(image_bytes) < 3000: continue 

                        b64 = base64.b64encode(image_bytes).decode("utf-8")
                        images_base64.append(b64)
                        logger.info(f"   🖼️ Extracted Image {len(images_base64)} from PDF Page {page_index+1}")
            except Exception as e:
                logger.error(f"   ❌ PDF Image Extraction Error: {e}")

        # 2. DOCX Image Extraction
        elif file_path.lower().endswith('.docx'):
            try:
                doc = Document(file_path)
                for rel in doc.part.rels.values():
                    if "image" in rel.target_ref:
                        image_bytes = rel.target_part.blob
                        
                        if len(image_bytes) < 3000: continue 

                        b64 = base64.b64encode(image_bytes).decode("utf-8")
                        images_base64.append(b64)
                        logger.info(f"   🖼️ Extracted Image {len(images_base64)} from DOCX")
            except Exception as e:
                logger.error(f"   ❌ DOCX Image Extraction Error: {e}")

    except Exception as e:
        logger.error(f"   ❌ General Image Extraction Error: {e}")

    return images_base64