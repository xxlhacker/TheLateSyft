import asyncio
import aiohttp
import requests
import json
import os
import sys
import logging
import subprocess
import config
import re


def make_results_dir():
    if not os.path.isdir(config.SYFT_RESULTS_DIR):
        os.makedirs(config.SYFT_RESULTS_DIR)


def osd_api_key_check():
    """
    Checks and vaildates OSD API Key that is supplied as an environment variable.
    """
    if config.OSD_API_KEY:
        headers = {"Authorization": f"Bearer {config.OSD_API_KEY}"}
        r = requests.get(config.PROD_OSD_API_URL, headers=headers)
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
        if os.path.exists(f"{config.WORKSTREAMS_DIR}/{sys.argv[1]}.json"):
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
    json_path = os.path.join(os.getcwd(), f"{config.WORKSTREAMS_DIR}/{sys.argv[1]}.json")
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
    async with aiohttp.ClientSession(headers={"Authorization": f"Bearer {config.OSD_API_KEY}"}) as session:
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


def clean_json(json_like):
    """
    Removes trailing commas from *json_like* and returns the result.  Example::
        >>> remove_trailing_commas('{"foo":"bar","baz":["blah",],}')
        '{"foo":"bar","baz":["blah"]}'
    https://gist.github.com/liftoff/ee7b81659673eca23cd9fc0d8b8e68b7
    """
    trailing_object_commas_re = re.compile(r'(,)\s*}(?=([^"\\]*(\\.|"([^"\\]*\\.)*[^"\\]*"))*[^"]*$)')
    trailing_array_commas_re = re.compile(r'(,)\s*\](?=([^"\\]*(\\.|"([^"\\]*\\.)*[^"\\]*"))*[^"]*$)')
    # Fix objects {} first
    objects_fixed = trailing_object_commas_re.sub("}", json_like)
    # Now fix arrays/lists [] and return the result
    return trailing_array_commas_re.sub("]", objects_fixed)


def syft_automation(deployment_data, csv_file_name, json_file_name):
    """
    Uses the deployment data collected from OSD and uses Syft to scan the identified images.
    Additionally, if any deployment uses a previously scanned image, it will use the cached
    results instead of rescanning.
    """
    syft_output_cache = {}
    with open(csv_file_name, "w") as file:
        file.write('"DEPLOYMENT NAME","QUAY TAG","PACKAGE NAME","VERSION INSTALLED","DEPENDENCY TYPE"')
    for deployment in deployment_data:
        deployment_name = deployment
        quay_url = deployment_data.get(deployment)
        if quay_url in syft_output_cache:
            logging.info(f"{deployment.upper()} uses a previously scanned image, using cached results.")
            with open(csv_file_name, "ab") as file:
                file.write(syft_output_cache[quay_url]["csv"])
            add_osd_metadata(deployment_name, quay_url, csv_file_name)
            with open(json_file_name, "ab") as file:
                file.write(syft_output_cache[quay_url]["json"])
        else:
            logging.info(f"Syfting through '{quay_url}'")
            command = f"syft {quay_url} -o template -t {config.TEMPLATES_DIR}/csv_and_json.tmpl"
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            output, _ = process.communicate()
            csv_output = output.split(b"===SYFT_TEMPLATE_SEPARATOR===")[0]
            # json_output = clean_json(output.split(b"===SYFT_TEMPLATE_SEPARATOR===")[1])
            json_output = output.split(b"===SYFT_TEMPLATE_SEPARATOR===")[1]
            syft_output_cache[quay_url] = {"csv": csv_output, "json": json_output}
            with open(csv_file_name, "ab") as file:
                file.write(csv_output)
            add_osd_metadata(deployment_name, quay_url, csv_file_name)
            with open(json_file_name, "ab") as file:
                file.write(json_output)
        add_osd_metadata(deployment_name, quay_url, json_file_name)


def add_osd_metadata(deployment_name, quay_url, file_name):
    """
    Looks at the provided output and replaces the "PLACEHOLDER" text with the associated
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
    Looks at the provided output and removes blank lines intoduced via Syft Output.
    """
    with open(file_name, "r") as file:
        filedata = file.readlines()
    with open(file_name, "w") as file:
        for line in filedata:
            if line != "\n":
                file.write(line)


def format_json(json_file_name):
    """
    Formats the JSON output file to make it vaild JSON
    """
    with open(json_file_name, "r") as file:
        filedata = file.read()
        clean_filedata = clean_json(f"[\n{filedata}]")
    with open(json_file_name, "w") as file:
        file.write(clean_filedata)


async def main():
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S", level=logging.INFO
    )
    osd_api_key_check()
    workstream_json_check()
    csv_file_name = f"{config.SYFT_RESULTS_DIR}/{sys.argv[1]}-sbom.csv"
    json_file_name = f"{config.SYFT_RESULTS_DIR}/{sys.argv[1]}-sbom.json"
    worksteam_json_data = define_component_list()
    make_results_dir()
    osd_results = await production_image_lookup(worksteam_json_data)
    deployment_data = osd_data_parser(osd_results)
    syft_automation(deployment_data, csv_file_name, json_file_name)
    remove_blank_lines(csv_file_name)
    remove_blank_lines(json_file_name)
    format_json(json_file_name)


if __name__ == "__main__":
    asyncio.run(main())
