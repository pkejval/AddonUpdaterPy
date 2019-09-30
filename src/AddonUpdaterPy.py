import os, sys, requests, re, json
from urllib.parse import urlparse
from AddonSites.IAddonSite import AddonSite
from AddonSites import *
import multiprocessing as mp
from urllib.request import urlopen
from urllib.error import URLError

# set this variable to False only for debugging purposes
MULTIPROCESS = True

WOW_PATH = ""
WOW_VERSION = "retail"
WOW_INTERFACE_PATH = ""
SAVEFILE_PATH = ""
addons = []
installed_addons = {}

interactive = True

addon_sites = []
for site in AddonSite.__subclasses__():
    addon_sites.append(site("","", ""))

def internet_on():
    """Checks for internet connection by opening
    google.com page.
    """
    for timeout in [1,5,10]:
        try:
            print("Waiting for internet connection with timeout " + str(timeout) + "s")
            urlopen('https://google.com',timeout=timeout)
            return True
        except URLError: pass
    return False

def myexit(exit_code=0):
    """Exits program with exit code. Waits for user input
    when global variable interactive is True
    """
    global interactive
    if interactive:
        input("\nPress ENTER key to exit...")
    
    sys.exit(exit_code)

def worker(procnum, addon, return_dict):
    """Worker function for multithreading addon.Update()
    """
    try:
        addon.Update()
    except Exception as e:
        print(e)

    return_dict[procnum] = addon

def main():
    global addons
    global interactive
    global installed_addons

    print("---------------------")
    print("| WoW Addon updater |")
    print("|     by Bugsa      |")
    print("---------------------\n")

    # parse input arguments
    if len(sys.argv) > 1 and (sys.argv[1] == "--script" or sys.argv[1] == "-s"): 
         interactive = False

    # check if internet connection is available before updating
    if not internet_on():
        print("Internet connection isn't available!")
        myexit(3)

    # exit when config.txt file isn't present and create example file
    if not os.path.exists("config.txt"):
        print("config.txt not found, creating example file")
        with (open("config.txt", "w")) as file:
            file.write("# Set path to your World of Warcraft installation\n")
            file.write("WOW_PATH=C:\\Program Files\\World of Warcraft\n")
            file.write("# Set WoW version - possible values are 'retail' or 'classic'\n")
            file.write("WOW_VERSION=retail\n")
            file.write("\n")
            file.write("# Set list of addons URLs - delimited by new line (ENTER)\n")
        myexit(5)

    read_config("config.txt")

    if not os.path.exists(WOW_PATH) or not os.path.exists(WOW_INTERFACE_PATH):
        print("Path to World of Warcraft installation isn't valid!")
        myexit(1)

    print("Found " + str(len(addons)) + " addons to install/update")
    print("WoW version is set to '" + WOW_VERSION + "'")
    print("WoW path is set to '" + WOW_INTERFACE_PATH + "'")

    installed_addons = read_installed_addons()
    
    print("\nStarting install/update")

    pool = []
    manager = mp.Manager()
    return_dict = manager.dict()
    i = 0
    for addon in addons:
        addon.installed_version = installed_addons.get(addon.url, "")
        if MULTIPROCESS:
            pool.append(mp.Process(target=worker, args=(i,addon,return_dict)))
            i+=1
        else:
            try:
                addon.Update()
            except Exception as e:
                print(e)

    if MULTIPROCESS:
        for p in pool:
            p.start()

        for p in pool:
            p.join()

    addons = return_dict.values()
    save_addon_status()

def read_config(path):
    """Reads and parses config file. This function sets global variables WOW_PATH,
     WOW_VERSION, WOW_INTERFACE_PATH, SAVEFILE_PATH and addons
    """
    global WOW_PATH
    global WOW_VERSION
    global WOW_INTERFACE_PATH
    global SAVEFILE_PATH
    global addons

    print("Reading config.txt")

    path_regex = re.compile("wow_path=", re.I)
    version_regex = re.compile("wow_version=", re.I)
    http_regex = re.compile("http://|https://", re.I)
    with open(path, 'r') as config:
        for line in config:
            line = line.strip()
            # skip comment line
            if line.startswith("#") or line == "": continue
            # parse WOW_PATH
            elif path_regex.match(line):
                WOW_PATH = line.strip().split("=")[1]
            # parse WOW_VERSION, should be retail or classic
            elif version_regex.match(line):
                WOW_VERSION = line.strip().split("=")[1].lower()
                if WOW_VERSION != "retail" or WOW_VERSION != 'classic': WOW_VERSION = "retail"
            # parse addon site URL
            elif http_regex.match(line):
                addon = create_addon_instance(line)
                if addon:
                    # add only if URL isn't duplicate
                    if not any(x for x in addons if x.url == addon.url): addons.append(addon)
            else:
                print("Bad config.txt line: '" + line + "'\n")
                

    WOW_INTERFACE_PATH = os.path.join(WOW_PATH, "_" + WOW_VERSION + "_", "Interface", "Addons")
    SAVEFILE_PATH = os.path.join(WOW_INTERFACE_PATH, "AddonUpdater.json")

def save_addon_status():
    """Save installed addons dictionary {URL, VERSION} to JSON savefile
    """
    global addons
    save = {}
    for addon in addons:
        if addon.installed_version != "":
            save[addon.url] = addon.installed_version #.append({"url": addon.url, "ver": addon.installed_version})
    
    with open(SAVEFILE_PATH, 'w') as outfile:
        json.dump(save, outfile)

def read_installed_addons():
    """Read and returns dictionary {URL, VERSION} of installed addons from JSON savefile
    """
    installed_addons = {}
    if not os.path.exists(SAVEFILE_PATH): 
        print(SAVEFILE_PATH + " not found")
        return
    
    print("Reading " + SAVEFILE_PATH)

    with open(SAVEFILE_PATH, 'r') as infile:
        installed_addons = json.load(infile)

    print("Found " + str(len(installed_addons)) + " installed addons")
    return installed_addons

def create_addon_instance(url):
    """Search for addonsite modules which inherits IAddonSite class and return instance of type
    that can handle such addonsite
    """
    parsed_url = urlparse(url)
    
    # Search for class that can handle URL and create new instance of it
    match = next((s for s in addon_sites if parsed_url.netloc in s.HandleURLs()), None)
    new_type = type(match)
    return new_type(url, parsed_url, WOW_PATH, WOW_VERSION)

if __name__ == "__main__":
    mp.freeze_support()
    main()
    myexit(0)