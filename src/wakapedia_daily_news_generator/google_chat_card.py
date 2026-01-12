"""
Google Chat Card formatting for Wakapedia Daily News.
Uses Google Chat's Card V2 format for rich message display.
"""

from datetime import datetime


def create_newsletter_card(
    news_title: str,
    news_content: str,
    news_link: str = None,
    tool_title: str = "",
    tool_content: str = "",
    tool_link: str = None,
    fun_content: str = ""
) -> dict:
    """
    Create a Google Chat Card V2 formatted message for the newsletter.

    Returns a dict that can be sent as JSON to Google Chat webhook.
    """
    # Format date in French
    today = datetime.now()
    days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    months_fr = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    date_str = f"{days_fr[today.weekday()]} {today.day} {months_fr[today.month - 1]} {today.year}"

    # Build the card structure
    card = {
        "cardsV2": [
            {
                "cardId": "wakapedia-daily-news",
                "card": {
                    "header": {
                        "title": "🗞️ Wakapedia Daily News",
                        "subtitle": f"L'agitateur matinal Tech & Fun • {date_str}",
                        "imageUrl": "https://raw.githubusercontent.com/waka-theo/wakapedia-daily-news/main/public/wakastellar.png",
                        "imageType": "CIRCLE"
                    },
                    "sections": [
                        # Daily News Section
                        {
                            "header": "📰 DAILY NEWS",
                            "collapsible": False,
                            "widgets": [
                                {
                                    "decoratedText": {
                                        "topLabel": "",
                                        "text": f"<b>{news_title}</b>",
                                        "wrapText": True
                                    }
                                },
                                {
                                    "textParagraph": {
                                        "text": news_content
                                    }
                                }
                            ]
                        },
                        # Divider
                        {
                            "widgets": [
                                {"divider": {}}
                            ]
                        },
                        # Daily Tool Section
                        {
                            "header": "🛠️ DAILY TOOL",
                            "collapsible": False,
                            "widgets": [
                                {
                                    "decoratedText": {
                                        "topLabel": "",
                                        "text": f"<b>{tool_title}</b>",
                                        "wrapText": True
                                    }
                                },
                                {
                                    "textParagraph": {
                                        "text": tool_content
                                    }
                                }
                            ]
                        },
                        # Divider
                        {
                            "widgets": [
                                {"divider": {}}
                            ]
                        },
                        # Daily Fun Fact Section
                        {
                            "header": "😄 DAILY FUN FACT",
                            "collapsible": False,
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": f"<i>{fun_content}</i>"
                                    }
                                }
                            ]
                        },
                        # Footer
                        {
                            "widgets": [
                                {"divider": {}},
                                {
                                    "decoratedText": {
                                        "text": "<font color=\"#666666\">WAKASTELLAR • Votre dose quotidienne de tech</font>",
                                        "wrapText": True
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }

    # Add link button to news section if provided
    if news_link:
        card["cardsV2"][0]["card"]["sections"][0]["widgets"].append({
            "buttonList": {
                "buttons": [
                    {
                        "text": "Lire l'article →",
                        "onClick": {
                            "openLink": {
                                "url": news_link
                            }
                        }
                    }
                ]
            }
        })

    # Add link button to tool section if provided
    if tool_link:
        card["cardsV2"][0]["card"]["sections"][2]["widgets"].append({
            "buttonList": {
                "buttons": [
                    {
                        "text": "Découvrir l'outil →",
                        "onClick": {
                            "openLink": {
                                "url": tool_link
                            }
                        }
                    }
                ]
            }
        })

    return card


def create_simple_card(
    news_title: str,
    news_content: str,
    tool_title: str,
    tool_content: str,
    fun_content: str,
    news_link: str = None,
    tool_link: str = None
) -> dict:
    """
    Create a simpler card format that's more compatible.
    """
    today = datetime.now()
    days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    months_fr = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    date_str = f"{days_fr[today.weekday()]} {today.day} {months_fr[today.month - 1]} {today.year}"

    # News section widgets
    news_widgets = [
        {
            "keyValue": {
                "topLabel": news_title,
                "content": news_content,
                "contentMultiline": True
            }
        }
    ]

    # Add news link button if provided
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

    # Tool section widgets
    tool_widgets = [
        {
            "keyValue": {
                "topLabel": tool_title,
                "content": tool_content,
                "contentMultiline": True
            }
        }
    ]

    # Add tool link button if provided
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

    return {
        "cards": [
            {
                "header": {
                    "title": "🗞️ Wakapedia Daily News",
                    "subtitle": date_str,
                    "imageUrl": "https://raw.githubusercontent.com/waka-theo/wakapedia-daily-news/main/public/wakastellar.png",
                    "imageStyle": "AVATAR"
                },
                "sections": [
                    {
                        "header": "<font color=\"#e74c3c\"><b>📰 DAILY NEWS</b></font>",
                        "widgets": news_widgets
                    },
                    {
                        "header": "<font color=\"#27ae60\"><b>🛠️ DAILY TOOL</b></font>",
                        "widgets": tool_widgets
                    },
                    {
                        "header": "<font color=\"#f39c12\"><b>😄 DAILY FUN FACT</b></font>",
                        "widgets": [
                            {
                                "textParagraph": {
                                    "text": fun_content
                                }
                            }
                        ]
                    },
                    {
                        "widgets": [
                            {
                                "textParagraph": {
                                    "text": "<font color=\"#95a5a6\"><i>WAKASTELLAR • L'agitateur matinal Tech & Fun</i></font>"
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }
