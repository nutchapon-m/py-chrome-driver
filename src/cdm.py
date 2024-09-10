from typing import Optional

import os
import platform
import zipfile
import shutil
import logging

import requests
from interface import DriverManager

logger = logging.getLogger()
    
    
class ChromeDriverManager(DriverManager):
    source_url = "https://googlechromelabs.github.io/chrome-for-testing"
    
    def __init__(
        self,
        driver_version: Optional[str] = None,
    ) -> None:
        
        if driver_version is None:
            self.driver_version: str = self.source_url + "/last-known-good-versions-with-downloads.json"
            self.fixSpec = False
        else:
            self.driver_version: str = self.source_url + f"/{driver_version}.json"
            self.fixSpec = True
        
        self.rootDir: str = os.getcwd()
        self.version: str = ""
        self.chromedriver_file_name: str = ""
        self.achieveFolder: str = ""

    @property
    def version(self) -> str:
        return self.__version
    
    @version.setter
    def version(self, version: str) -> None:
        self.__version = version

    @property
    def chromedriver_file_name(self) -> str:
        return self.__chromedriver_file_name
    
    @chromedriver_file_name.setter
    def chromedriver_file_name(self, chromedriver_file_name: str) -> None:
        self.__chromedriver_file_name = chromedriver_file_name
    
    @property
    def achieveFolder(self) -> str:
        return self.__achieveFolder

    @achieveFolder.setter
    def achieveFolder(self, achieveFolder: str) -> None:
        self.__achieveFolder = achieveFolder


    def rename_directory(self, old_name:str, new_name:str) -> None:
        try:
            # Rename the directory
            os.rename(old_name, new_name)
            logger.info(f'Directory renamed from [{old_name.split("/")[-1]}] => [{new_name.split("/")[-1]}]')
        except FileNotFoundError:
            logger.info(f'Error: The directory "{old_name}" does not exist.')
        except PermissionError:
            logger.info('Error: You do not have permission to rename the directory.')
        except Exception as e:
            logger.info(f'An error occurred: {e}')

    @property
    def get_os(self):
        os_name = platform.system()
        if os_name == 'Darwin':
            return 'mac-x64'
        elif os_name == 'Linux':
            return 'linux64'
        else:
            return 'Other'
    
    @property
    def check_exit_folder(self):
        folder_path = f'{self.rootDir}/chromedriver'
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            return "ok"
        else:
            raise Exception("Folder does not exist.")
    
    @property
    def check_exit_chrome_driver(self):
        folder_path = f'{self.rootDir}/chromedriver/{self.version}'
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            return 1
        else:
            return 0
        
    def getDownloadUrlList(self, json: dict[str,]) -> str:
        if self.fixSpec:
            self.version = json['version']
            downloadList = json['downloads']['chromedriver']
            logger.info(f"Found ChromeDriver version => [{self.version}]")
        else:
            channels: dict = json.get("channels")
            stableVersion = channels.get("Stable")
            # Set version chromedriver.
            self.version = stableVersion['version']
            downloadList = stableVersion['downloads']['chromedriver']
            logger.info(f"Found ChromeDriver version => [{self.version}]")
        return downloadList

    def getChromeDrvierUrl(self, session: requests.Session):
        try:
            _os = self.get_os
            if isinstance(_os, str) and _os == 'Other':
                raise Exception("Get Os Error.")
            logger.info(f"Operation System => {_os}")
            # Download Link Version Chrome Driver
            logger.debug(type(session))
            resp = session.get(self.driver_version)
            if resp.status_code == 200:
                json_object: dict = resp.json()
                downloadList = self.getDownloadUrlList(json_object)

                # Check exit chromedriver
                exit = self.check_exit_chrome_driver
                if exit:
                    logger.info("ChromeDriver is available.")
                    return None
                
                # Find chromedriver that match os system.
                for pf in downloadList:
                    if pf['platform'] ==  _os:
                        url: str = pf['url']
                        # Set achieve folder
                        self.achieveFolder = url.split("/")[-1].split(".")[0]
                        logger.info(f"Set achieve folder => [{self.achieveFolder}]")
            else:
                logger.error(f"Error status code => {resp.status_code}")

            logger.info("Get Url Success.")
            return url
        except Exception as e:
            logger.error(e)
            raise e

    def downloadChromeDriver(self, session: requests.Session ,url: str):
        # Download Chrome Driver
        if isinstance(url, str):
            resp = session.get(url)
            if resp.status_code == 200:
                filename = url.split("/")[-1]
                # Check exiting folder
                try:
                    result = self.check_exit_folder
                    if isinstance(result, str):
                        pass
                except:
                    os.mkdir(f"{self.rootDir}/chromedriver")

                # Save the file
                with open(f"{self.rootDir}/chromedriver/{filename}", 'wb') as file:
                    file.write(resp.content)
            else:
                raise Exception(resp.status_code)
            
        return filename
    

    def extract_zip(self, filename: str) -> str | None:
        # Define file to extract.
        file_to_extract = f"{self.achieveFolder}/chromedriver"
        # Define ZIP file path location.
        zip_file_path = f"{self.rootDir}/chromedriver/{filename}"
        # Define target path to unzip file.
        destination_path = f"{self.rootDir}/chromedriver"
        
        # Check exiting ZIP file.
        if not os.path.exists(zip_file_path):
            logger.error(f"File not found: {zip_file_path}")
            return None

        # Open ZIP file,
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Achieve ZIP to targer folder.
            if file_to_extract in zip_ref.namelist():
                zip_ref.extract(file_to_extract, destination_path)
        
        # Convert to executable file
        taget_file = f"{self.rootDir}/chromedriver/{file_to_extract}"
        with open(taget_file, 'rb') as bf:
            buffer = bf.read()
        with open(taget_file, 'wb') as wf:
            wf.write(buffer)
        os.chmod(taget_file, 0o755)
        return "ok"
    
        
    def install(self):
        with requests.Session() as session:
            try:
                url = self.getChromeDrvierUrl(session)
                if isinstance(url, str):
                    filename = self.downloadChromeDriver(session, url)
                    if isinstance(filename, str):
                        logger.info("Download ChromeDriver Success!!!")
                else:
                    return f"{self.rootDir}/chromedriver/{self.version}/chromedriver"
            except Exception as e:
                if isinstance(e, int):
                    logger.error(f"Error Download ChromeDriver status {e}.")
                    raise Exception(f"Error Download ChromeDriver status {e}.")
                else:
                    logger.exception(e)
                
        result = self.extract_zip(filename)
        if isinstance(result, str):
            logger.info("Create ChromeDriver Binary Executable Success!!!")
        # Rename foldername to version
        self.rename_directory(f"chromedriver/{self.achieveFolder}", f"chromedriver/{self.version}")
        # Delete ZIP file
        os.remove(f"chromedriver/{self.achieveFolder}.zip")
        logger.info("Process done")
        return f"{self.rootDir}/chromedriver/{self.version}/chromedriver"
    
    def clear(self) -> None:
        shutil.rmtree(f"{self.rootDir}/chromedriver")

    @property
    def get_driver(self):
        return "chromedriver/*/chromedriver"