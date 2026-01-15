"""
Google Chat Card formatting for Wakapedia Daily News.
Uses Google Chat's Card V1 format for webhook compatibility.
"""

from datetime import datetime


def create_simple_card(
    news_title: str,
    news_content: str,
    tool_title: str,
    tool_content: str,
    fun_content: str,
    news_link: str = None,
    tool_link: str = None,
    logo_url: str = None
) -> dict:
    """
    Create a Google Chat Card V1 formatted message for the newsletter.
    This format works with incoming webhooks.
    """
    # Format date in French
    today = datetime.now()
    days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    months_fr = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    date_str = f"{days_fr[today.weekday()]} {today.day} {months_fr[today.month - 1]} {today.year}"

    # Build sections
    sections = []

    # === DAILY NEWS Section ===
    news_widgets = [
        {
            "textParagraph": {
                "text": "<font color=\"#e74c3c\"><b>📰 DAILY NEWS</b></font>"
            }
        },
        {
            "textParagraph": {
                "text": f"<b>{news_title}</b>"
            }
        },
        {
            "textParagraph": {
                "text": news_content
            }
        }
    ]
    if news_link:
        news_widgets.append({
            "buttons": [
                {
                    "textButton": {
                        "text": "📖 LIRE L'ARTICLE",
                        "onClick": {
                            "openLink": {
                                "url": news_link
                            }
                        }
                    }
                }
            ]
        })
    sections.append({"widgets": news_widgets})

    # === DAILY TOOL Section ===
    tool_widgets = [
        {
            "textParagraph": {
                "text": "<font color=\"#27ae60\"><b>🛠 DAILY TOOL</b></font>"
            }
        },
        {
            "textParagraph": {
                "text": f"<b>{tool_title}</b>"
            }
        },
        {
            "textParagraph": {
                "text": tool_content
            }
        }
    ]
    if tool_link:
        tool_widgets.append({
            "buttons": [
                {
                    "textButton": {
                        "text": "🔗 DÉCOUVRIR L'OUTIL",
                        "onClick": {
                            "openLink": {
                                "url": tool_link
                            }
                        }
                    }
                }
            ]
        })
    sections.append({"widgets": tool_widgets})

    # === DAILY FUN FACT Section ===
    sections.append({
        "widgets": [
            {
                "textParagraph": {
                    "text": "<font color=\"#f39c12\"><b>😄 DAILY FUN FACT</b></font>"
                }
            },
            {
                "textParagraph": {
                    "text": f"{fun_content} 🐛"
                }
            }
        ]
    })

    # === Footer Section ===
    sections.append({
        "widgets": [
            {
                "textParagraph": {
                    "text": "<i>WAKASTELLAR • L'agitateur matinal Tech & Fun</i>"
                }
            }
        ]
    })

    # Build header with optional logo
    header = {
        "title": "Wakapedia Daily News",
        "subtitle": date_str
    }
    
    if logo_url:
        header["imageUrl"] = logo_url
        header["imageStyle"] = "IMAGE"  # "IMAGE" = rectangulaire, "AVATAR" = rond
    
    return {
        "cards": [
            {
                "header": header,
                "sections": sections
            }
        ]
    }
