"""
Resume export utilities.

Exports optimized resume in multiple formats: DOCX, PDF, and TXT.
Handles file creation and directory management.
"""

import os
import uuid
from typing import Optional
from pathlib import Path
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from utils.constants import OUTPUT_DIR, SUPPORTED_EXPORT_FORMATS, DEFAULT_EXPORT_FORMAT
from utils.logger import get_logger

logger = get_logger(__name__)


def export_to_docx(text: str, output_path: str) -> str:
    """
    Export resume to DOCX format.
    
    Args:
        text: Resume text content
        output_path: Full output file path
        
    Returns:
        Output file path
        
    Raises:
        IOError: If file write fails
    """
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        doc = Document()
        
        for line in text.split("\n"):
            line = line.strip()
            if line:
                doc.add_paragraph(line)
        
        doc.save(output_path)
        logger.info(f"Exported DOCX to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"DOCX export failed: {e}")
        raise IOError(f"Failed to export DOCX: {e}")


def export_to_pdf(text: str, output_path: str) -> str:
    """
    Export resume to PDF format.
    
    Args:
        text: Resume text content
        output_path: Full output file path
        
    Returns:
        Output file path
        
    Raises:
        IOError: If file write fails
    """
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        c = canvas.Canvas(output_path, pagesize=letter)
        
        width, height = letter
        x = 50
        y = height - 50
        line_height = 14
        
        for line in text.split("\n"):
            if y < 50:
                c.showPage()
                y = height - 50
            
            # Truncate long lines to fit page width
            line_text = line[:100].strip()
            if line_text:
                c.drawString(x, y, line_text)
                y -= line_height
        
        c.save()
        logger.info(f"Exported PDF to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise IOError(f"Failed to export PDF: {e}")


def export_to_txt(text: str, output_path: str) -> str:
    """
    Export resume to TXT format.
    
    Args:
        text: Resume text content
        output_path: Full output file path
        
    Returns:
        Output file path
        
    Raises:
        IOError: If file write fails
    """
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        logger.info(f"Exported TXT to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"TXT export failed: {e}")
        raise IOError(f"Failed to export TXT: {e}")


def export_resume(text: str, output_format: str = DEFAULT_EXPORT_FORMAT) -> str:
    """
    Export resume in selected format.
    
    Supports: DOCX, PDF, TXT
    
    Args:
        text: Resume text content
        output_format: Export format (docx, pdf, or txt)
        
    Returns:
        Path to exported file
        
    Raises:
        ValueError: If format is unsupported
        IOError: If export fails
    """
    output_format = output_format.lower().strip()
    
    if output_format not in SUPPORTED_EXPORT_FORMATS:
        raise ValueError(
            f"Unsupported export format: {output_format}. "
            f"Supported: {', '.join(SUPPORTED_EXPORT_FORMATS)}"
        )
    
    if not text or not text.strip():
        raise ValueError("Cannot export empty resume")
    
    logger.info(f"Exporting resume as {output_format}")
    
    # Generate output filename
    unique_id = uuid.uuid4().hex[:10]
    filename = f"final_resume_{unique_id}.{output_format}"
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    try:
        if output_format == "docx":
            return export_to_docx(text, output_path)
        elif output_format == "pdf":
            return export_to_pdf(text, output_path)
        elif output_format == "txt":
            return export_to_txt(text, output_path)
    except Exception as e:
        logger.error(f"Export failed for format {output_format}: {e}")
        raise