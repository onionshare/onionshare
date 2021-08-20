#!/usr/bin/env python3
import sys
import httpx
import asyncio
import time


api_token = None
languages = {}
app_translations = {}
docs_translations = {}


async def api(path):
    url = f"https://hosted.weblate.org{path}"

    async with httpx.AsyncClient() as client:
        r = await client.get(
            url, headers={"Authorization": f"Token {api_token}"}, timeout=30.0
        )

    if r.status_code == 200:
        print(f"GET {url}")
        return r.json()
    else:
        print(f"GET {url} | error {r.status_code}")
        return None


async def get_app_translation(lang_code):
    global app_translations
    obj = await api(f"/api/translations/onionshare/translations/{lang_code}/")
    if obj:
        app_translations[lang_code] = obj["translated_percent"]


async def get_docs_translation(component, lang_code):
    global docs_translations
    obj = await api(f"/api/translations/onionshare/{component}/{lang_code}/")
    if obj:
        if component not in docs_translations:
            docs_translations[component] = {}
        docs_translations[component][lang_code] = obj["translated_percent"]


async def app_percent_output(percent_min, percent_max=101):
    out = []
    for lang_code in languages:
        if (
            app_translations[lang_code] >= percent_min
            and app_translations[lang_code] < percent_max
        ):
            out.append(
                f"{languages[lang_code]} ({lang_code}), {app_translations[lang_code]}%"
            )

    out.sort()

    print(f"App translations >= {percent_min}%")
    print("=======================")
    print("\n".join(out))

    print("")


async def docs_percent_output(percent_min, exclude=[]):
    out = []
    for lang_code in languages:
        include_language = True
        percentages = []

        for component in docs_translations:
            if lang_code not in docs_translations[component]:
                include_language = False
                break

            percentages.append(docs_translations[component][lang_code])

            if docs_translations[component][lang_code] < percent_min:
                include_language = False
                break

        if include_language:
            percentages = [f"{p}%" for p in percentages]
            percentages = ", ".join(percentages)
            out.append(f"{languages[lang_code]} ({lang_code}), {percentages}")

    excluded = []
    for s in out:
        if s not in exclude:
            excluded.append(s)

    excluded.sort()

    print(f"Docs translations >= {percent_min}%")
    print("========================")
    print("\n".join(excluded))

    print("")
    return excluded


async def main():
    global api_token, languages, app_translations, docs_translations

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} API_KEY")
        print(
            "You can find your personal API key at: https://hosted.weblate.org/accounts/profile/#api"
        )
        return

    api_token = sys.argv[1]

    # Get the list of languages in the OnionShare project
    res = await api("/api/projects/onionshare/languages/")
    for obj in res:
        languages[obj["code"]] = obj["language"]

    # Get the app translations for each language
    await asyncio.gather(*[get_app_translation(lang_code) for lang_code in languages])

    # Get the documentation translations for each component for each language
    for component in [
        "doc-advanced",
        "doc-develop",
        "doc-features",
        "doc-help",
        "doc-index",
        "doc-install",
        "doc-security",
        "doc-sphinx",
        "doc-tor",
    ]:
        docs_futures = []
        for lang_code in languages:
            docs_futures.append(get_docs_translation(component, lang_code))

        await asyncio.gather(*docs_futures)

    print("")

    await app_percent_output(100)
    await app_percent_output(90, 100)
    await app_percent_output(80, 90)

    out100 = await docs_percent_output(100)
    out90 = await docs_percent_output(90, out100)
    await docs_percent_output(80, out100 + out90)


if __name__ == "__main__":
    asyncio.run(main())
