# AddonUpdaterPy
Simple addon updater for World of Warcraft. Do you hate to have Twitch/TukUI clients running in background to update your addons? I do! That's why I created this project - just update my addons and exit! 

Supports most popular addon sites:
* www.curseforge.com
* www.wowace.com
* wowinterface.com
* tukui.org

## Installation
Download AddonUpdaterPy.exe and run it. It will create example "config.txt" file

## Configuration
Open "config.txt" in your favourite text editor and specify path to your World of Warcraft folder and World of Warcraft version - "retail" or "classic".
Go to your favourite addon website and copy URLs of addons which should be installed/updated.

Example "config.txt":
```
# Set path to your World of Warcraft installation
WOW_PATH=C:\Program Files (x86)\Battle.NET\World of Warcraft
# Set WoW version - possible values are 'retail' or 'classic' - defaults to 'retail' if not set
WOW_VERSION=retail

# Set list of addons URLs - delimited by new line (ENTER)
https://wow.curseforge.com/projects/plater-nameplates
https://wowinterface.com/downloads/info8814-DeadlyBossMods.html
https://www.tukui.org/download.php?ui=elvui
https://www.tukui.org/addons.php?id=38
```

## Startup
You can run application directly from executable in "console interactive mode". Progress will be output to console window. Updater stops when finished and shows summary about installed/updated/error addons and waits for user interaction.

### Automatic update
Best usage scenario of this app is run it automatically from Windows Task Scheduler on every computer startup or user login.
If you want to run application from script or Task Scheduler, just run it with **--script** or **-s** parameter. It will automatically close AddonUpdater window after work is done.

## Limitations
* You can update addons in only one World of Warcraft installation at once. If you need update more, you need copy AddonUpdaterPy to separate folder and set its own "config.txt" file.
* Application should be multi-platform compatible but for now it's tested and released only for **Windows**.

## Contribution
If you want to contribute either by finding and reporting Issues or you came just with new idea - do it please! Pull requests are welcome too!

### How to add support for another addon site
Create new file in AddonSites folder and create new class which inherits from AddonSite base class (interface) and implement three methods:

1. **GetURL** - You can transform URL provided from "config.txt". Function must return URL in string format. AddonUpdater will use it for fetch addon website.
2. **LookupNewVersion** - This function gets "html" variable which is instance of BeautifulSoup with loaded HTML response from addon site. You can use BeautifulSoup methods on HTML data in "html" variable and parse information from it. You have to set these variables for updater to work:
    * **self.name** - Addon name
    * **self.available_version** - Newest version found at addon website
    * **self.download_url** - URL for download newest version of addon
3. **HandleURLs** - Must return list of strings (hostnames) which module can handle (**without** 'http://' or 'https://' part)
