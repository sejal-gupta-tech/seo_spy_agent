import uuid

from jinja2 import Environment, FileSystemLoader

from app.core.config import PROJECT_ROOT, REPORTS_DIR, TEMPLATES_DIR
from app.core.logger import logger


def render_report_html(data: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("report.html")
    return template.render(data)


def generate_pdf_report(html_content: str) -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    task_id = str(uuid.uuid4())
    pdf_path = REPORTS_DIR / f"{task_id}.pdf"
    html_path = REPORTS_DIR / f"{task_id}.html"

    # Try WeasyPrint first (best quality)
    try:
        from weasyprint import HTML
        HTML(string=html_content, base_url=str(PROJECT_ROOT)).write_pdf(str(pdf_path))
        logger.info("PDF generated at %s using WeasyPrint", pdf_path)
        return task_id
    except (ImportError, Exception) as e:
        logger.warning("WeasyPrint failed (likely missing GTK): %s. Trying xhtml2pdf fallback...", str(e))

    # Try xhtml2pdf as fallback (no native dependencies)
    try:
        from xhtml2pdf import pisa
        with pdf_path.open("wb") as f:
            pisa_status = pisa.CreatePDF(html_content, dest=f)
        
        if not pisa_status.err:
            logger.info("PDF generated at %s using xhtml2pdf fallback", pdf_path)
            return task_id
        else:
            logger.error("xhtml2pdf failed to generate PDF: %s", pisa_status.err)
    except Exception as e:
        logger.error("xhtml2pdf fallback failed: %s", str(e))

    # Final fallback: save HTML instead
    try:
        with html_path.open("w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info("HTML fallback saved at %s", html_path)
        return task_id
    except Exception as e:
        logger.error("All PDF/HTML generation attempts failed: %s", str(e))
        return task_id
