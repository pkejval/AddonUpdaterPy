from abc import ABC, abstractmethod
import cfscrape, tempfile, zipfile, os, random, string
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class VersionException(Exception):
    pass

class AddonSite(ABC):
    def __init__(self, url, parsed_url, wow_path, wow_version = "retail"):
        self.url = url
        self.parsed_url = parsed_url
        self.name = ""
        self.installed_version = ""
        self.available_version = ""
        self.download_url = ""
        self.wow_path = wow_path
        self.wow_version = wow_version
        self.tempfile = ""
        self.scraper = cfscrape.create_scraper()
    
    def __str__(self):
        if self.name != "": return self.name
        else: return self.url

    def GetHostname(self):
        return self.parsed_url.hostname

    def GetSchemeWithHostname(self):
        return self.parsed_url.scheme + "://" + self.GetHostname()

    def GetHTMLPage(self):
        page = self.scraper.get(self.GetURL())
        if page.status_code == 404:
            raise Exception("[ERROR] " + self.url + " - URL isn't valid")
        return BeautifulSoup(page.content, 'html.parser')

    def DownloadFile(self):
        if self.download_url == "": raise Exception("Download URL not found")
        if self.installed_version == self.available_version and self.available_version != "": 
            print("[UP-TO-DATE] " + self.name)
            return

        cffile = self.scraper.get(self.download_url)
        self.tempfile = tempfile.mkstemp(suffix = '.zip')[1]
        with open(self.tempfile, 'wb') as temp:
            temp.write(cffile.content)
        
        self.UnzipFile()

    def UnzipFile(self):
        if not os.path.exists(self.tempfile): raise Exception
        with zipfile.ZipFile(self.tempfile, 'r') as zip:
            zip.extractall(os.path.join(self.wow_path, "_" + self.wow_version + "_", "Interface", "Addons"))
        
        if self.installed_version == "": print("[INSTALLED] " + self.name)
        else: print("[UPDATED] " + self.name)
        self.installed_version = self.available_version

    def Update(self):
        try:
            self.LookupNewVersion(self.GetHTMLPage())
        except VersionException as ve:
            print("[ERROR] " + self.url + " - " + str(ve))
            return
        except Exception:
            print("[ERROR] " + self.url + " - problem parsing HTML page")
            return

        try:
            self.DownloadFile()
        except Exception:
            print("[ERROR] " + self.name + " - cannot download file")

    @abstractmethod
    def GetURL(self):
        raise NotImplementedError

    @abstractmethod
    def LookupNewVersion(self, html):
        raise NotImplementedError

    @abstractmethod
    def HandleURLs(self):
        raise NotImplementedError