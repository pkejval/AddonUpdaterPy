from AddonSites.IAddonSite import AddonSite

class Curse(AddonSite):
    def GetURL(self):
        # wow.curseforge.com redirects to www.curseforge.com with different path
        if self.parsed_url.hostname == "wow.curseforge.com":
            self.parsed_url = self.parsed_url._replace(netloc="www.curseforge.com")
            self.parsed_url = self.parsed_url._replace(path=self.parsed_url.path.replace("projects", "wow/addons"))

        return self.parsed_url.geturl() + "/files?sort=releasetype"

    def LookupNewVersion(self, html):
        self.name = html.find("h2", {"class": "font-bold text-lg break-all"}).text.strip()    
        rows = html.find_all("tr")

        for row in rows:
            game_version = row.find("div", {"class": "mr-2"})
            if not game_version: continue
            if self.wow_version == "retail" and game_version.text.strip().startswith("1."): continue
            data = row.find("a", {"data-action": "file-link"})
            self.available_version = data.text.strip()
            self.download_url = self.GetSchemeWithHostname() + data.attrs["href"].replace("files", "download") + "/file"
            break     

    def HandleURLs(self):
        return ["wow.curseforge.com", "www.curseforge.com"]