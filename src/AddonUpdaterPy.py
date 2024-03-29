import os, sys, requests, re, json, getopt, shutil, tempfile, win32api, subprocess
from urllib.parse import urlparse
from AddonSites.IAddonSite import AddonSite
from AddonSites import *
import multiprocessing as mp
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError

# set this variable to tag new release for autoupdating
APP_VERSION=0.6

# set this variable to False only for debugging purposes
MULTIPROCESS = True

WOW_PATH = ""
WOW_VERSION = "retail"
WOW_INTERFACE_PATH = ""
SAVEFILE_PATH = ""
addons = []
installed_addons = {}

DEBUG = False
interactive = True

addon_sites = []
for site in AddonSite.__subclasses__():
    addon_sites.append(site("","", ""))

def check_update(this_path):
    """ Checks github release. If newer version found (by tag), download and update itself """
    try:
        version_regex= re.compile("\/tag\/(.*)")
        html = urlopen("https://github.com/pkejval/AddonUpdaterPy/releases/latest")
        version = float(version_regex.search(html.url).group(1))

        if (version > APP_VERSION):
            print("New version '" + str(version) + "' is available! Starting update...")
            temp = os.path.join(tempfile.gettempdir(), "AddonUpdaterPy.exe")
            print("Downloading update...")
            urlretrieve("https://github.com/pkejval/AddonUpdaterPy/releases/download/" + str(version) + "/AddonUpdaterPy.exe", temp)           
            subprocess.Popen([temp, '--update=' + this_path], shell=True)
            sys.exit(0)

    except Exception as e: print("Check update: " + str(e)); myexit(1)

def do_update(this_path, path):
    """Copy current running script file into path to update binary and starts it """
    try:
        print("Copying " + this_path + " into " + path)
        shutil.copyfile(this_path, path)
        subprocess.Popen(path, shell=True)
        sys.exit(0)
    except Exception as e: print("do_update: " + str(e)); myexit(1)

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
    global MULTIPROCESS
    global DEBUG
    can_update = True

    print("---------------------")
    print("| WoW Addon updater |")
    print("|     by Bugsa      |")
    print("---------------------\n")
    print("Version " + str(APP_VERSION))

    this_path = win32api.GetLongPathName(sys.argv[0]) if '~' in sys.argv[0] else sys.argv[0]

    # parse input arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "siu:dn", ["script", "singlethread", "update=", "debug", "noupdate"])
    except Exception as e:
        print(str(e))
        myexit(2)

    for opt, arg in opts:
        if opt in ("-s", "--script"):
            interactive = False
        elif opt in ("-i", "--singlethread"):
            MULTIPROCESS = False
        elif opt in ("u", "--update"):
            do_update(this_path, arg)
            sys.exit(0)
        elif opt in ("d", "--debug"):
            DEBUG = True
        elif opt in ("n", "--noupdate"):
            can_update = False

    # check if internet connection is available before updating
    if not DEBUG and not internet_on():
        print("Internet connection isn't available!")
        myexit(3)

    if not DEBUG and can_update: check_update(this_path);

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
        if installed_addons:
            if addon.url in installed_addons:
                data = installed_addons[addon.url]
                if "folders" in data: addon.old_folders = data["folders"]
                if "installed_version" in data: addon.installed_version = data["installed_version"]

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
    
    # cleanup temp files
    for addon in addons:
        try:
            addon.RemoveTempFile()
        except: pass

    # remove folders of addons that were installed but already not present in config.txt
    if installed_addons:
        uninstall = [item for item in installed_addons if item not in [a.url for a in addons]]
        for u in uninstall:
            for folder in installed_addons[u]["folders"]:
                shutil.rmtree(os.path.join(WOW_INTERFACE_PATH, folder), ignore_errors=False)
                while os.path.exists(os.path.join(WOW_INTERFACE_PATH, folder)): pass
            print("[UNINSTALLED] - " + u)

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

    path_regex = re.compile("wow_path=(.*)", re.I)
    version_regex = re.compile("wow_version=(.*)", re.I)
    http_regex = re.compile("http://|https://", re.I)
    with open(path, 'r') as config:
        for line in config:
            line = line.strip()
            # skip comment line
            if line.startswith("#") or line == "": continue
            
            # search addon URL
            elif match := http_regex.match(line):
                addon = create_addon_instance(match.string)
                if addon:
                    # add only if URL isn't duplicate
                    if not any(x for x in addons if x.url == addon.url): addons.append(addon)
            
            # parse WOW_PATH
            elif match := path_regex.match(line):
                WOW_PATH = match.groups(1)[0]
            
            # parse WOW_VERSION, should be retail or classic
            elif match := version_regex.match(line):
                WOW_VERSION = match.groups(1)[0]
                if WOW_VERSION != "retail" or WOW_VERSION != 'classic': WOW_VERSION = "retail"

            else: print("Bad config.txt line: '" + line + "'\n")

    WOW_INTERFACE_PATH = os.path.join(WOW_PATH, "_" + WOW_VERSION + "_", "Interface", "Addons")
    SAVEFILE_PATH = os.path.join(WOW_INTERFACE_PATH, "AddonUpdater.json")

def save_addon_status():
    """Save installed addons dictionary {URL, VERSION} to JSON savefile
    """
    global addons
    save = {}
    for addon in addons:
        if addon.installed_version != "":
            save[addon.url] = {
                "installed_version" : addon.installed_version,
                "folders": addon.new_folders
                }
    
    with open(SAVEFILE_PATH, 'w') as outfile:
        json.dump(save, outfile)

def read_installed_addons():
    """Read and returns dictionary {URL, VERSION} of installed addons from JSON savefile
    """
    installed_addons = {}
    
    if not os.path.exists(SAVEFILE_PATH): 
        print(SAVEFILE_PATH + " not found")
        return installed_addons
    
    try:
        with open(SAVEFILE_PATH, 'r') as infile:
            installed_addons = json.load(infile)
    except: pass

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