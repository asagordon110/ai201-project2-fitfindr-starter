import os
from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings


load_dotenv()


def search_listings(description, size=None, max_price=None):
    """
    Search mock listings by description, optional size, and max price.
    Returns a list of matching listing dictionaries.
    """
    listings = load_listings()

    if not description:
        return []

    description_words = description.lower().split()
    results = []

    for item in listings:
        title = item.get("title", "").lower()
        item_description = item.get("description", "").lower()
        category = item.get("category", "").lower()
        style_tags = " ".join(item.get("style_tags", [])).lower()

        searchable_text = f"{title} {item_description} {category} {style_tags}"

        matches_description = any(word in searchable_text for word in description_words)

        matches_size = True
        if size:
            matches_size = item.get("size", "").lower() == size.lower()

        matches_price = True
        if max_price is not None:
            matches_price = float(item.get("price", 0)) <= float(max_price)

        if matches_description and matches_size and matches_price:
            score = sum(1 for word in description_words if word in searchable_text)
            item_copy = item.copy()
            item_copy["_score"] = score
            results.append(item_copy)

    results.sort(key=lambda item: item["_score"], reverse=True)

    for item in results:
        item.pop("_score", None)

    return results


def _get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("Missing GROQ_API_KEY. Add it to your .env file.")

    return Groq(api_key=api_key)


def suggest_outfit(new_item, wardrobe):
    """
    Suggest an outfit using the selected listing and the user's wardrobe.
    Returns a styling suggestion string.
    """
    if not new_item:
        return "I need a selected item before I can suggest an outfit."

    wardrobe_items = wardrobe.get("items", []) if wardrobe else []

    if wardrobe_items:
        wardrobe_text = "\n".join(
            [
                f"- {item.get('name')} ({item.get('category')}): "
                f"colors={item.get('colors')}, style_tags={item.get('style_tags')}, notes={item.get('notes')}"
                for item in wardrobe_items
            ]
        )
    else:
        wardrobe_text = (
            "The user's wardrobe is empty, so give general styling advice based on the new item."
        )

    prompt = f"""
You are FitFindr, a helpful secondhand fashion styling assistant.

New item:
{new_item}

User wardrobe:
{wardrobe_text}

Suggest one complete outfit using the new item. If wardrobe items are available, mention specific pieces from the wardrobe. If the wardrobe is empty, give general styling advice.

Keep the response practical, stylish, and concise.
"""

    try:
        client = _get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a concise fashion styling assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"I couldn't generate an outfit suggestion right now. Error: {e}"


def create_fit_card(outfit, new_item):
    """
    Create a short shareable outfit caption.
    Returns a caption-style string.
    """
    if not outfit or not outfit.strip():
        return "I need an outfit suggestion before I can create a fit card."

    if not new_item:
        return "I need a selected item before I can create a fit card."

    prompt = f"""
Create a short, casual, social-media-style outfit caption.

New thrifted item:
{new_item}

Outfit:
{outfit}

Requirements:
- 1 sentence only
- casual and stylish
- not too formal
- mention the thrifted item or the outfit vibe
- make it sound like something someone would post online
"""

    try:
        client = _get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You write short stylish outfit captions."},
                {"role": "user", "content": prompt},
            ],
            temperature=1.0,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"I couldn't create a fit card right now. Error: {e}"