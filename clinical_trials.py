import os
import asyncio
from unidecode import unidecode
import nodriver as uc
from pyvirtualdisplay import Display
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime


load_dotenv(override=True)

clinical_trials = [
    {"nct_id": "NCT05392712", "version": 2},
    {"nct_id": "NCT04305366", "version": 1},
    {"nct_id": "NCT04368728", "version": 1},
]


async def eligibility_scraping():
    try:
        display = None
        browser = None

        if os.getenv("LINUX") == "yes":
            display = Display(visible=0, size=(1920, 1080))
            display.start()

        browser = await uc.start(
            headless=False,
            # user_data_dir= os.getcwd() + "/profile", # by specifying it, it won't be automatically cleaned up when finished
            # browser_executable_path="/path/to/some/other/browser",
            # browser_args=['--some-browser-arg=true', '--some-other-option'],
            lang="en-US",  # this could set iso-language-code in navigator, it was not recommended to change according to docs            no_sandbox=True,
        )
        eligibility_data = {}  # Final JSON, structured { NCT1: {field: val,...}, NCT2: {field: val,...}}
        for trial in clinical_trials:
            tab = await browser.get(
                f"https://clinicaltrials.gov/study/{trial.get('nct_id')}?tab=history&a={trial.get('version')}#version-content-panel"
            )
            await asyncio.sleep(2)
            await tab.select("body")
            await tab.scroll_down(100)
            await tab.scroll_down(200)

            elig_titles = await tab.select_all("#eligibility-card .cell.title-cell div")
            elig_content = await tab.select_all(
                "#eligibility-card .cell.content-cell .text-cell"
            )

            trial_eligi = {}

            for title, content in zip(elig_titles, elig_content):
                key = title.text_all
                value = content.text_all
                if key:
                    trial_eligi[key] = value

            eligibility_data[trial.get("nct_id")] = trial_eligi

        # Output to csv
        df = pd.DataFrame.from_dict(eligibility_data, orient="index")
        df.to_csv(
            f"output/run_{str(datetime.now()).replace(' ', '_').replace(':', '_').replace('.', '_')}.csv",
            index=True,
        )

        # Close tabs and browser properly
        await tab.close()
        browser.stop()

        if display:
            display.stop()

    except Exception as e:
        if browser:
            browser.stop()
            print(e)
        if display:
            display.stop()
            print(e)


if __name__ == "__main__":
    asyncio.run(eligibility_scraping())
