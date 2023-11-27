#!env python3
import requests
from packaging.version import parse, InvalidVersion
from bs4 import BeautifulSoup
import argparse
import json
import sys


def get_latest_atlassian_version(product_name, is_lts):
    """
    Fetches the latest version of an Atlassian product.

    Args:
    product_name: Name of the product ('jira', 'confluence', 'jira-service-desk').
    is_lts: Flag indicating whether to fetch the LTS version or not.

    Returns:
    The latest version of the product or an error message.
    """
    # URLs for different Atlassian products
    urls = {
        "jira": "https://my.atlassian.com/download/feeds/current/jira-software.json",
        "confluence": "https://my.atlassian.com/download/feeds/current/confluence.json",
        "jira-service-desk": "https://my.atlassian.com/download/feeds/current/jira-servicedesk.json"
    }

    if product_name in urls:
        url = urls[product_name]

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = json.loads(response.text[10:-1])  # Parsing the JSON

            versions = [item for item in data if ('Enterprise' in item['edition']) == is_lts]
            versions.sort(key=lambda x: parse(x['version']), reverse=True)

            return versions[0]['version'] if versions else "No valid version found"

        except requests.exceptions.RequestException as e:
            return f"UNKNOWN: Request error - {e}"
    else:
        return "Product not found. Please check the product name."


def check_atlassian_product_version(base_url, product, auth=None):
    """
    Checks the installed version of an Atlassian product.

    Args:
    base_url: Base URL of the Atlassian server.
    product: Name of the product ('jira', 'confluence', 'jira-service-desk').
    auth: Authentication details.

    Returns:
    The installed version of the product or an error message.
    """
    api_endpoints = {
        'jira': '/rest/api/2/serverInfo',
        'confluence': '/',  # Main page for Confluence
        'jira-service-desk': '/rest/servicedeskapi/info'
    }

    if product in api_endpoints:
        api_url = base_url + api_endpoints[product]

        try:
            response = requests.get(api_url, auth=auth)
            response.raise_for_status()

            if product == 'jira':
                data = response.json()
                return data['version']
            elif product == 'jira-service-desk':
                data = response.json()
                return data['version'].split('-')[0]  # ugly hack against service desk versions like 5.11.3-REL-0001
            elif product == 'confluence':
                # Parsing HTML to get Confluence version
                soup = BeautifulSoup(response.text, 'html.parser')
                version_tag = soup.find('meta', {'name': 'ajs-version-number'})
                return version_tag.attrs['content'] if version_tag else "Version not found"

        except requests.exceptions.RequestException as e:
            return f"UNKNOWN: Request error - {e}"
    else:
        return "Unknown product"


def compare_versions(installed_version, latest_version):
    """
    Compares two versions of products.

    Args:
    installed_version: The installed version.
    latest_version: The latest available version.

    Returns:
    The result of comparison ('OK', 'WARNING', 'CRITICAL', 'UNKNOWN').
    """
    try:
        installed = parse(installed_version)
        latest = parse(latest_version)
    except InvalidVersion:
        return 'UNKNOWN' if installed_version != latest_version else 'OK'

    if installed.major < latest.major or installed.minor < latest.minor:
        return 'CRITICAL'
    elif installed.micro < latest.micro:
        return 'WARNING'
    else:
        return 'OK'


def main():
    """
    Main function of the script.
    """
    parser = argparse.ArgumentParser(description="Atlassian Product Version Checker for Nagios/Icinga")
    parser.add_argument('-H', '--host', required=True, help='Hostname to check')
    parser.add_argument('--software', required=True, choices=['jira', 'confluence', 'jira-service-desk'],
                        help='Type of Atlassian software')
    parser.add_argument('-S', '--ssl', action='store_true', help='Use SSL for connection')
    parser.add_argument('--auth', help='Optional authentication string for Atlassian software')
    parser.add_argument('--lts', action='store_true', help='Check for LTS version if set, non-LTS otherwise')
    args = parser.parse_args()

    # Construct the base URL
    protocol = 'https' if args.ssl else 'http'
    base_url = f"{protocol}://{args.host}"

    # Fetch the installed and latest versions
    installed_version = check_atlassian_product_version(base_url, args.software, args.auth)
    latest_version = get_latest_atlassian_version(args.software, args.lts)
#    print(f"installed {installed_version} latest {latest_version}")
    # Compare the versions
    result = compare_versions(installed_version, latest_version)

    # Print the result and exit with the appropriate status code
    if result == 'OK':
        print(f"OK: Installed version {installed_version} is up-to-date")
        sys.exit(0)
    elif result == 'WARNING':
        print(f"WARNING: Installed version {installed_version} differs in patch version from the latest {latest_version}")
        sys.exit(1)
    elif result == 'CRITICAL':
        print(f"CRITICAL: Installed version {installed_version} is significantly out of date compared to the latest {latest_version}")
        sys.exit(2)
    else:  # UNKNOWN
        print(f"UNKNOWN: Error encountered - {installed_version}")
        sys.exit(3)


if __name__ == "__main__":
    main()
