"""
PLEASE NOTE:
This python script is meant to be run by its parent script, "jenkins-job.sh". If you plan on 
running this python script independently, you will need to create the "/syft_results" 
directory if it does not already exist.
"""

import asyncio
import aiohttp
import requests
import json
import os
import sys
import logging
import subprocess


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
            quit()
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
        urls.extend(url for url in component.values() if url != "")
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
    Parses through returns OSD data and builds a dictionary of Pod Names and Quay Image Tag to be used by Syft.
    """
    deployment_data = {}
    for components in osd_results:
        if components["kind"] == "Deployment":
            for component in components["spec"]["template"]["spec"]["containers"]:
                deployment_data[component["name"]] = component["image"]
        elif components["kind"] == "CronJob":
            deployment_data[component["name"]] = components["spec"]["jobTemplate"]["spec"]["template"]["spec"][
                "containers"
            ][0]["image"]
        elif components["kind"] == "Status" and components["reason"] == "NotFound":
            logging.error(
                f'Deployment {components["details"]["name"].upper()} was not found in OSD. '
                "Please check the associated workstream template and verify all OSD URLs are correct."
            )
    return deployment_data


def syft_automation(deployment_data, file_name):
    """
    Uses the deployment data collected from OSD and uses Syft to scan the identified images.
    Additionally, if any deployment uses a previously scanned image, it will use the cached
    results instead of rescanning.
    """
    syft_output_cache = {}
    with open(file_name, "w") as file:
        file.write('"DEPLOYMENT NAME","QUAY TAG","PACKAGE NAME","VERSION INSTALLED","DEPENDENCY TYPE"')
    for deployment in deployment_data:
        deployment_name = deployment
        quay_url = deployment_data.get(deployment)
        if quay_url in syft_output_cache:
            logging.info(f"{deployment.upper()} uses a previously scanned image, using cached results.")
            with open(file_name, "ab") as file:
                file.write(syft_output_cache[quay_url])
                add_osd_metadata(deployment_name, quay_url, file_name)
        else:
            logging.info(f"Syfting through '{quay_url}'")
            command = f"syft {quay_url} -o template -t templates/csv.tmpl"
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            output, _ = process.communicate()
            syft_output_cache[quay_url] = output
            with open(file_name, "ab") as file:
                file.write(output)
            add_osd_metadata(deployment_name, quay_url, file_name)


def add_osd_metadata(deployment_name, quay_url, file_name):
    """
    Looks at the output CSV and replaces the "PLACEHOLDER" text with the associated
    OSD metadata.
    """
    with open(file_name, "r") as file:
        filedata = file.read()
    filedata = filedata.replace("DEPLOYMENT_NAME_PLACEHOLDER", deployment_name)
    filedata = filedata.replace("QUAY_TAG_PLACEHOLDER", quay_url)
    with open(file_name, "w") as file:
        file.write(filedata)


def remove_blank_lines(file_name):
    """
    Looks at the output CSV and removes blank lines intoduced via Syft Output.
    """
    with open(file_name, "r") as file:
        filedata = file.readlines()
    with open(file_name, "w") as file:
        for line in filedata:
            if line != "\n":
                file.write(line)


async def main():
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S", level=logging.INFO
    )
    osd_api_key_check()
    workstream_json_check()
    file_name = f"syft_results/{sys.argv[1]}-sbom.csv"
    worksteam_json_data = define_component_list()
    osd_results = await production_image_lookup(worksteam_json_data)
    deployment_data = osd_data_parser(osd_results)
    syft_automation(deployment_data, file_name)
    remove_blank_lines(file_name)


if __name__ == "__main__":
    asyncio.run(main())
