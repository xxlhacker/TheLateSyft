import asyncio
import aiohttp
import requests
import json
import os
import sys
import logging
from pprint import pprint as ppp


def osd_api_key_check():
    """
    Checks and vaildates OSD API Key that is supplied as an environment variable.
    """
    if "OSD_API_KEY" in os.environ:
        url = "https://api.crcp01ue1.o9m8.p1.openshiftapps.com:6443/"
        headers = {"Authorization": f"Bearer {os.environ['OSD_API_KEY']}"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            logging.info("OSD Prod Authentication Successful!")
        else:
            logging.error('OSD Prod Authentication was unsuccessful, please varify your "OSD API KEY" is vaild.')
    else:
        logging.error('Job Failed to start. You must supply an "OSD_API_KEY" as environment variable.')
        quit()


def workstream_json_check():
    """
    Checks and validates the existance of the workstream json name supplied via command line argument.
    """
    if len(sys.argv) > 1:
        if os.path.exists(f"workstreams/{sys.argv[1]}.json"):
            logging.info("Workstream JSON Found!")
        else:
            logging.error("Unable to find Workstream JSON.")
            quit()
    else:
        logging.error('Job Failed to start. You must supply a supported "WORKSTEAM" as command line argument.')
        quit()


def define_component_list():
    """
    Opens and reads the OSD urls for each component with the supplied workstream JSON.
    """
    json_path = os.path.join(os.getcwd(), f"workstreams/{sys.argv[1]}.json")
    with open(json_path, "r") as json_file:
        return json.loads(json_file.read())


async def production_image_lookup(worksteam_json_data):
    """
    Pulls deployement data from OSD for each component based on the supplied workstream JSON.
    """
    osd_results = []
    urls = []
    for component in worksteam_json_data["components"]:
        for url in component.values():
            if url != "":
                urls.append(url)
    async with aiohttp.ClientSession(headers={"Authorization": f'Bearer {os.environ["OSD_API_KEY"]}'}) as session:
        tasks = get_tasks(session, urls)
        responses = await asyncio.gather(*tasks)
        for response in responses:
            osd_results.append(await response.json())
    return osd_results


def get_tasks(session, urls):
    """
    Sets up Async task for production_image_lookup.
    """
    return [session.get(url, ssl=True) for url in urls]


def osd_data_parser(osd_results):
    """
    Parses through returns OSD data and build and dedups a list of Quay Image Tag to be used by Syft.
    """
    quay_urls = {}
    for components in osd_results:
        if components["kind"] == "Deployment":
            for component in components["spec"]["template"]["spec"]["containers"]:
                quay_urls[component["name"]] = component["image"]
        elif components["kind"] == "CronJob":
            quay_urls[component["name"]] = components["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][
                0
            ]["image"]
    return quay_urls


async def main():
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S", level=logging.INFO
    )
    osd_api_key_check()
    workstream_json_check()
    worksteam_json_data = define_component_list()
    osd_results = await production_image_lookup(worksteam_json_data)
    quay_urls = osd_data_parser(osd_results)
    ppp(quay_urls, sort_dicts=False)


if __name__ == "__main__":
    asyncio.run(main())
