import os
from typing import Optional
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# -------------------------------------------------------------------------
# Perception Module: Resume Loader
# -------------------------------------------------------------------------
def read_resume_file(file_path: str) -> str:
    """Reads a resume file (PDF or Text) and returns its content as a string."""
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"

    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.pdf':
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif ext in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return f"Error: Unsupported file format {ext}. Please provide .pdf, .txt, or .md."
    except Exception as e:
        return f"Error reading file: {str(e)}"

# -------------------------------------------------------------------------
# Action Module: PDF Generator
# -------------------------------------------------------------------------
def generate_resume_pdf(content: str, output_path: str = "optimized_resume.pdf") -> str:
    """Generates a PDF file from the provided text content."""
    try:
        # Register a font that supports Chinese if possible (using a default system font fallback or standard)
        # Note: ReportLab default fonts don't support Chinese. 
        # For this demo, we will try to use a standard font or just ASCII if no Chinese font is available.
        # In a real env, we'd bundle a font like 'SimHei.ttf'.
        # 这里尝试注册一种支持中文的字体，如果不存在则回退。
        # Windows通常有 SimHei 或 Microsoft YaHei
        
        font_name = "Helvetica" # Default fallback
        
        # Try to find a Chinese font on Windows
        windows_fonts = ["C:\\Windows\\Fonts\\simhei.ttf", "C:\\Windows\\Fonts\\msyh.ttf"]
        for font_path in windows_fonts:
            if os.path.exists(font_path):
                try:
                    font_name = "CustomFont"
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    break
                except:
                    continue
        
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Create a custom style that uses our font
        style = ParagraphStyle(
            name='Normal_Custom',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=12,
            leading=18,
            spaceAfter=10
        )
        
        title_style = ParagraphStyle(
            name='Title_Custom',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            leading=22,
            spaceAfter=20,
            alignment=1 # Center
        )

        story = []
        
        # Simple Markdown-like parsing (very basic)
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 12))
                continue
            
            if line.startswith('# '):
                story.append(Paragraph(line[2:], title_style))
            elif line.startswith('## '):
                # Sub-heading
                sub_style = ParagraphStyle(
                    name='Sub_Custom',
                    parent=styles['Heading2'],
                    fontName=font_name,
                    fontSize=14,
                    leading=18,
                    spaceAfter=12,
                    textColor=colors.darkblue
                )
                story.append(Paragraph(line[3:], sub_style))
            else:
                # Handle bullet points simply
                if line.startswith('- ') or line.startswith('* '):
                    line = '&bull; ' + line[2:]
                
                # Replace newlines with <br/> is not needed as we split by lines, 
                # but ReportLab Paragraph handles wrapping.
                story.append(Paragraph(line, style))

        doc.build(story)
        return f"Successfully generated PDF at: {os.path.abspath(output_path)}"
        
    except Exception as e:
        return f"Error generating PDF: {str(e)}"

if __name__ == "__main__":
    # Test perception
    # with open("test.txt", "w", encoding="utf-8") as f: f.write("Hello World")
    # print(read_resume_file("test.txt"))
    
    # Test action
    # print(generate_resume_pdf("# Resume\n\n## Experience\n- Worked at AI Co.", "test_output.pdf"))
    pass
