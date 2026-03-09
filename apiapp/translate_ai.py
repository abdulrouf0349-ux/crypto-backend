from googletrans import Translator
import time

translator = Translator()

def translate_to_lang(text, target="ur"):
    """Translate text to the target language using Google Translate."""
    try:
        translated = translator.translate(text, dest=target).text
        time.sleep(0.3)  # rate limit to avoid blocking
        return translated
    except Exception as e:
        print(f"[ERROR] Translation failed for {target}: {e}")
        return text
