from AddonSites.IAddonSite import AddonSite

class WoWAce(AddonSite):
    def GetURL(self):
        return self.url + "/files?sort=releasetype"

    def LookupNewVersion(self, html):
        self.name = html.find("h1", {"class": "project-title"}).text.strip()    
        rows = html.find_all("tr", {"class": "project-file-list-item"})

        for row in rows:
            game_version = row.find("span", {"class": "version-label"}).text.strip()
            if self.wow_version == "retail" and game_version.startswith("1."): continue
            data = row.find("div", {"class": "project-file-name-container"})
            self.available_version = data.text.strip()
            self.download_url = self.GetSchemeWithHostname() + data.find("a").attrs["href"] + "/download"
            break     

    def HandleURLs(self):
        return ["wowace.com", "www.wowace.com"]