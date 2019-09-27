from AddonSites.IAddonSite import AddonSite, VersionException

class TukUI(AddonSite):
    def GetURL(self):
        return self.url

    def get_addons_info(self, html):
        self.name = html.find("span", {"class": "Member"}).text.strip()
        self.available_version = html.find("b", {"class": "VIP"}).text.strip()
        self.download_url = self.url.replace("id", "download")

    def LookupNewVersion(self, html):        
        if self.wow_version == "retail":     

            if self.parsed_url.path == "/download.php":
                self.name = html.find("h1", {"class": "notice"}).text.strip()
                self.available_version = html.find("b", {"class": "Premium"}).text.strip()
                self.download_url = self.GetSchemeWithHostname() + html.find("a", {"class": "btn-large"}).attrs["href"]

            elif self.parsed_url.path == "/addons.php":
                self.get_addons_info(html)

            elif self.parsed_url.path == '/classic-addons.php':
                raise VersionException("URL isn't for 'retail' version")
              
        elif self.wow_version == "classic":

            if self.parsed_url.path == "/classic-addons.php":
                self.get_addons_info(html)
            elif self.parsed_url.path == "/download.php":
                raise VersionException("URL isn't for 'classic' version")
   
    def HandleURLs(self):
        return ["tukui.org", "www.tukui.org"]