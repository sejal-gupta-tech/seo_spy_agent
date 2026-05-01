import uuid
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.core.config import PROJECT_ROOT, REPORTS_DIR, TEMPLATES_DIR
from app.core.logger import logger


def render_report_html(data: dict, template_name: str = "report.html") -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template(template_name)
    return template.render(data)


def _delete_if_empty(path: Path) -> None:
    try:
        if path.exists() and path.stat().st_size == 0:
            path.unlink()
    except OSError:
        logger.warning("Failed to remove empty file at %s", path)


def generate_pdf_report(
    html_content: str,
    fallback_html_content: str | None = None,
) -> str:
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
        logger.warning("WeasyPrint not available: %s. Trying xhtml2pdf fallback...", str(e))

    # Try xhtml2pdf as fallback (no native dependencies)
    fallback_source = fallback_html_content or html_content
    try:
        from xhtml2pdf import pisa
        with pdf_path.open("wb") as f:
            pisa_status = pisa.CreatePDF(
                fallback_source,
                dest=f,
                encoding="utf-8",
            )

        if not pisa_status.err and pdf_path.exists() and pdf_path.stat().st_size > 0:
            logger.info("PDF generated at %s using xhtml2pdf fallback", pdf_path)
            return task_id
        else:
            logger.error("xhtml2pdf failed to generate PDF: %s", pisa_status.err)
    except ImportError:
        logger.warning("xhtml2pdf not installed, skipping PDF generation")
    except Exception as e:
        logger.error("xhtml2pdf fallback failed: %s", str(e))

    _delete_if_empty(pdf_path)

    # Final fallback: save HTML instead (always works)
    try:
        with html_path.open("w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info("HTML report saved at %s (PDF libraries not available)", html_path)
        return task_id
    except Exception as e:
        logger.error("All PDF/HTML generation attempts failed: %s", str(e))
        return task_id
