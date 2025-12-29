import os
import markdown
from typing import Optional
from pypdf import PdfReader
from xhtml2pdf import pisa
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
# Action Module: PDF Generator (Markdown -> PDF)
# -------------------------------------------------------------------------
def generate_resume_pdf(content: str, output_path: str = "optimized_resume.pdf") -> str:
    """
    Generates a PDF file from the provided Markdown content using xhtml2pdf.
    Supports basic Markdown syntax and Chinese characters (if font is available).
    """
    print(f"DEBUG: Starting PDF generation. Output path: {output_path}")
    try:
        # 1. Register a Chinese font using reportlab
        font_name = None
        
        # Check for local font first (most reliable)
        local_font_path = os.path.join(os.getcwd(), "fonts", "ChineseFont.ttf")
        print(f"DEBUG: Checking local font path: {local_font_path}")
        if os.path.exists(local_font_path):
             try:
                # Use a simple name without spaces
                font_name = "ChineseFont"
                pdfmetrics.registerFont(TTFont(font_name, local_font_path))
                print(f"DEBUG: Registered local font successfully: {local_font_path} as {font_name}")
             except Exception as e:
                 print(f"DEBUG: Failed to register local font: {e}")
                 font_name = None
        else:
            print("DEBUG: Local font file not found.")

        if not font_name:
            # Fallback to system fonts
            windows_fonts = [
                ("SimHei", "C:\\Windows\\Fonts\\simhei.ttf"),
                ("MicrosoftYaHei", "C:\\Windows\\Fonts\\msyh.ttf"),
                ("SimSun", "C:\\Windows\\Fonts\\simsun.ttc")
            ]
            
            for name, path in windows_fonts:
                if os.path.exists(path):
                    try:
                        # Register font
                        pdfmetrics.registerFont(TTFont(name, path))
                        font_name = name
                        print(f"DEBUG: Registered system font: {path} as {font_name}")
                        break
                    except Exception as e:
                        print(f"DEBUG: Failed to register system font {path}: {e}")
                        continue
        
        body_font_family = "sans-serif"
        
        if font_name:
            body_font_family = f"'{font_name}', sans-serif"
            print(f"DEBUG: Using font family: {body_font_family}")
        else:
            print("DEBUG: No Chinese font registered. Using default sans-serif.")
        
        # 2. Convert Markdown to HTML
        html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])

        # 3. Create full HTML document with CSS
        # We add a generic @font-face just in case, pointing to the local file if available,
        # to double-ensure xhtml2pdf picks it up.
        font_face_css = ""
        if font_name == "ChineseFont" and os.path.exists(local_font_path):
             # Use forward slashes for CSS url
             css_path = local_font_path.replace("\\", "/")
             if not css_path.startswith("file:///"):
                 css_path = "file:///" + css_path
             
             font_face_css = f"""
                @font-face {{
                    font-family: 'ChineseFont';
                    src: url('{css_path}');
                }}
             """
             print(f"DEBUG: Added @font-face CSS pointing to {css_path}")

        full_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                {font_face_css}
                * {{
                    font-family: {body_font_family};
                }}
                body {{
                    font-family: {body_font_family};
                    font-size: 12pt;
                    line-height: 1.5;
                    margin: 40px;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    font-family: {body_font_family};
                }}
                p, div, span, li, ul, ol, table, td, th, strong, em, code, pre {{
                    font-family: {body_font_family};
                }}
                h1 {{
                    font-size: 24pt;
                    border-bottom: 2px solid #333;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                h2 {{
                    font-size: 16pt;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 5px;
                    margin-top: 20px;
                    margin-bottom: 10px;
                    color: #2c3e50;
                }}
                h3 {{
                    font-size: 14pt;
                    margin-top: 15px;
                    margin-bottom: 5px;
                    color: #34495e;
                }}
                p {{
                    margin-bottom: 10px;
                    text-align: justify;
                }}
                ul {{
                    margin-bottom: 10px;
                    padding-left: 20px;
                }}
                li {{
                    margin-bottom: 5px;
                }}
                code {{
                    background-color: #f4f4f4;
                    padding: 2px 4px;
                    border-radius: 4px;
                    font-family: monospace;
                }}
                strong {{
                    font-weight: bold;
                    color: #000;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # 4. Write PDF
        with open(output_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                src=full_html,
                dest=pdf_file,
                encoding='utf-8'
            )

        if pisa_status.err:
            return f"Error generating PDF: {pisa_status.err}"
            
        return f"Successfully generated PDF at: {os.path.abspath(output_path)}"
        
    except Exception as e:
        import traceback
        return f"Error generating PDF: {str(e)}\n{traceback.format_exc()}"

if __name__ == "__main__":
    pass
