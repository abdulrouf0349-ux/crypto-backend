import argostranslate.package
import argostranslate.translate

# Available packages download karo
argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()

# Jinhe chahiye install karo (en → target)
LANGS = ['ur', 'ru', 'ar', 'es', 'fr', 'de', 'zh']

for lang in LANGS:
    pkg = next(
        filter(lambda x: x.from_code == 'en' and x.to_code == lang, available_packages),
        None
    )
    if pkg:
        print(f"Installing en → {lang}...")
        argostranslate.package.install_from_path(pkg.download())
    else:
        print(f"Package not found: en → {lang}")