#!/usr/bin/env python3
import sys
import httpx
import asyncio


api_token = None
languages = {}
app_translations = {}
docs_translations = {}


async def api(path):
    url = f"https://hosted.weblate.org{path}"

    # Wait a bit before each API call, to avoid hammering the server and
    # getting temporarily blocked
    await asyncio.sleep(1)

    async with httpx.AsyncClient() as client:
        r = await client.get(
            url, headers={"Authorization": f"Token {api_token}"}, timeout=60
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
            lang_code in app_translations
            and app_translations[lang_code] >= percent_min
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


async def docs_percent_output(percent_min, percent_max=101):
    out = []
    for lang_code in languages:
        percentages = []

        for component in docs_translations:
            if lang_code in docs_translations[component]:
                percentages.append(docs_translations[component][lang_code])
            else:
                percentages.append(0)

        average_percentage = int(sum(percentages) / len(percentages))

        if (
            average_percentage != 0
            and average_percentage >= percent_min
            and average_percentage < percent_max
        ):
            out.append(f"{languages[lang_code]} ({lang_code}), {average_percentage}%")

    out.sort()

    print(f"Docs translations >= {percent_min}%")
    print("========================")
    print("\n".join(out))

    print("")


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
        languages[obj["code"]] = obj["name"]

    # Get the app translations for each language
    for lang_code in languages:
        await get_app_translation(lang_code)

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
        for lang_code in languages:
            await get_docs_translation(component, lang_code)

    print("")

    await app_percent_output(90, 101)
    await app_percent_output(50, 90)
    await app_percent_output(0, 50)

    await docs_percent_output(90, 101)
    await docs_percent_output(50, 90)
    await docs_percent_output(0, 50)


if __name__ == "__main__":
    asyncio.run(main())
