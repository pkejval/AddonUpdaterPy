from AddonSites.IAddonSite import AddonSite, VersionException
import re

class WoWInterface(AddonSite):
    def GetURL(self):
        return self.url

    def LookupNewVersion(self, html):
        if self.wow_version == "classic":        
            if not "classic" in html.find_all("td", {"class": "alt1"})[1].text.strip().lower():
                raise VersionException("URL isn't for 'classic' version of addon!")
        
        self.name = html.find("h1").text.strip()    
        self.available_version = html.find("div", {"id": "version"}).text.strip()
        id_regex = re.compile("info(\d+)\-", re.MULTILINE)
        number = id_regex.search(self.url)[1]
        self.download_url = "https://cdn.wowinterface.com/downloads/file" + number + "/"
       
    def HandleURLs(self):
        return ["wowinterface.com", "www.wowinterface.com"]