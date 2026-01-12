import os
import base64
from datetime import datetime
from weasyprint import HTML, CSS
from pathlib import Path


def get_newsletter_template() -> str:
    """Return the HTML template for the newsletter."""
    return '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wakapedia Daily News</title>
    <style>
        @page {
            size: A4;
            margin: 0;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }

        .newsletter {
            max-width: 100%;
            background: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header .logo-img {
            max-width: 180px;
            height: auto;
            margin-bottom: 15px;
        }

        .header h1 {
            font-size: 1.3em;
            font-weight: 600;
            margin-bottom: 6px;
            letter-spacing: 0.5px;
        }

        .header .subtitle {
            font-size: 0.85em;
            opacity: 0.8;
            font-weight: 300;
        }

        .header .date {
            margin-top: 12px;
            font-size: 0.8em;
            background: rgba(255,255,255,0.15);
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
        }

        .section {
            padding: 25px 30px;
            border-bottom: 1px solid #eee;
        }

        .section:last-child {
            border-bottom: none;
        }

        .section-header {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }

        .section-icon {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1em;
            margin-right: 10px;
            color: white;
        }

        .section-title {
            font-size: 0.7em;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 700;
        }

        .news .section-icon { background: linear-gradient(135deg, #ff6b6b, #ee5a5a); }
        .news .section-title { color: #ee5a5a; }

        .tool .section-icon { background: linear-gradient(135deg, #4ecdc4, #44a08d); }
        .tool .section-title { color: #44a08d; }

        .fun .section-icon { background: linear-gradient(135deg, #f7b733, #fc4a1a); }
        .fun .section-title { color: #e67e22; }

        .section h3 {
            font-size: 1.05em;
            color: #1a1a2e;
            margin-bottom: 8px;
            line-height: 1.4;
        }

        .section p {
            font-size: 0.9em;
            color: #555;
            line-height: 1.7;
        }

        .section a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }

        .fun-content {
            background: linear-gradient(135deg, #fff9e6, #fff3cd);
            padding: 18px;
            border-radius: 10px;
            text-align: center;
            font-size: 0.95em;
            color: #333;
            line-height: 1.6;
        }

        .footer {
            background: #f8f9fa;
            padding: 15px 30px;
            text-align: center;
            font-size: 0.75em;
            color: #888;
        }

        .footer .brand {
            font-weight: 700;
            color: #1a1a2e;
            font-size: 1em;
        }
    </style>
</head>
<body>
    <div class="newsletter">
        <div class="header">
            {logo_section}
            <h1>L'agitateur matinal de savoir Tech & Fun</h1>
            <div class="subtitle">pour la team Wakastellar</div>
            <div class="date">{date}</div>
        </div>

        <div class="section news">
            <div class="section-header">
                <div class="section-icon">📰</div>
                <div class="section-title">Daily News</div>
            </div>
            <h3>{news_title}</h3>
            <p>{news_content}</p>
        </div>

        <div class="section tool">
            <div class="section-header">
                <div class="section-icon">🛠️</div>
                <div class="section-title">Daily Tool</div>
            </div>
            <h3>{tool_title}</h3>
            <p>{tool_content}</p>
        </div>

        <div class="section fun">
            <div class="section-header">
                <div class="section-icon">😄</div>
                <div class="section-title">Daily Fun Fact</div>
            </div>
            <div class="fun-content">
                {fun_content}
            </div>
        </div>

        <div class="footer">
            <div class="brand">WAKASTELLAR</div>
            <div>Wakapedia Daily News - Votre dose quotidienne de tech</div>
        </div>
    </div>
</body>
</html>'''


def get_logo_base64() -> str:
    """Get the logo as base64 for embedding in HTML."""
    logo_path = Path(__file__).parent.parent.parent / "public" / "wakastellar.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode('utf-8')
        return f'<img src="data:image/png;base64,{logo_data}" alt="WAKASTELLAR" class="logo-img">'
    return '<div class="brand" style="font-size: 1.5em; margin-bottom: 15px;">WAKASTELLAR</div>'


def generate_pdf(
    news_title: str,
    news_content: str,
    tool_title: str,
    tool_content: str,
    fun_content: str,
    output_path: str = None
) -> str:
    """
    Generate a PDF newsletter from the provided content.

    Returns the path to the generated PDF.
    """
    # Format date in French
    date_fr = datetime.now().strftime("%A %d %B %Y").capitalize()

    # French day/month names
    days = {'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
            'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'}
    months = {'January': 'Janvier', 'February': 'Février', 'March': 'Mars', 'April': 'Avril',
              'May': 'Mai', 'June': 'Juin', 'July': 'Juillet', 'August': 'Août',
              'September': 'Septembre', 'October': 'Octobre', 'November': 'Novembre', 'December': 'Décembre'}

    for en, fr in days.items():
        date_fr = date_fr.replace(en, fr)
    for en, fr in months.items():
        date_fr = date_fr.replace(en, fr)

    # Get template and fill in content
    html_content = get_newsletter_template().format(
        logo_section=get_logo_base64(),
        date=date_fr,
        news_title=news_title,
        news_content=news_content,
        tool_title=tool_title,
        tool_content=tool_content,
        fun_content=fun_content
    )

    # Generate output path if not provided
    if output_path is None:
        output_dir = Path(__file__).parent.parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"wakapedia_daily_news_{datetime.now().strftime('%Y%m%d')}.pdf")

    # Generate PDF
    HTML(string=html_content).write_pdf(output_path)

    return output_path


def parse_crew_output(crew_result: str) -> dict:
    """
    Parse the crew output to extract individual sections.
    This is a simple parser - adjust based on actual crew output format.
    """
    # Default values
    result = {
        'news_title': 'Actualité du jour',
        'news_content': '',
        'tool_title': 'Outil du jour',
        'tool_content': '',
        'fun_content': ''
    }

    # The crew output is typically the final task result (newsletter HTML)
    # We need to extract the content from it or use the raw output
    # For now, return the raw content - this will be refined based on actual output

    return result
