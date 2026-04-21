from jinja2 import Environment, FileSystemLoader
import os
import uuid


def render_report_html(data: dict) -> str:
    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("report.html")
    return template.render(data)


def generate_pdf_report(html_content: str) -> str:
    os.makedirs("reports", exist_ok=True)

    task_id = str(uuid.uuid4())
    pdf_path = f"reports/{task_id}.pdf"
    html_path = f"reports/{task_id}.html"

    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(pdf_path)
        print(f"PDF generated: {pdf_path}")
        return task_id

    except Exception as e:
        print("PDF ERROR:", getattr(e, "message", repr(e)))

        # fallback: save HTML instead
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"HTML fallback saved: {html_path}")
        return task_id
