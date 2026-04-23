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

    try:
        from weasyprint import HTML

        HTML(string=html_content, base_url=str(PROJECT_ROOT)).write_pdf(str(pdf_path))
        logger.info("PDF generated at %s", pdf_path)
        return task_id

    except Exception:
        logger.exception("PDF generation failed. Saving HTML fallback instead.")

        # fallback: save HTML instead
        with html_path.open("w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info("HTML fallback saved at %s", html_path)
        return task_id
