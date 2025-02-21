import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os
from pathlib import Path
from tqdm import tqdm
import subprocess
from datetime import datetime

class GitManager:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.download_count = 0
        
    def commit_and_push(self, division_id):
        """Commit changes and push to GitHub"""
        try:
            # Change to repository directory
            current_dir = Path.cwd()
            os.chdir(self.repo_path)
            
            # Add all new files
            subprocess.run(['git', 'add', '.'], check=True)
            
            # Create commit message
            commit_msg = f"Update: Downloaded through division {division_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            
            # Push changes
            subprocess.run(['git', 'push'], check=True)
            
            print(f"\nSuccessfully pushed changes to GitHub at division {division_id}")
            
            # Change back to original directory
            os.chdir(current_dir)
            return True
        except Exception as e:
            print(f"Error pushing to GitHub: {e}")
            os.chdir(current_dir)
            return False
        
def check_division_exists(division_id, driver):
    """Check if a division exists by looking for specific elements"""
    try:
        url = f"https://votes.parliament.uk/votes/commons/division/{division_id}"
        driver.get(url)
        
        # Wait a short time for the download button
        # If it exists, this is a valid division page
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "get-files"))
        )
        return True
    except TimeoutException:
        # If we timeout waiting for the download button, the division probably doesn't exist
        try:
            # Check if we got the error page
            error_text = driver.find_element(By.TAG_NAME, "h1").text
            if "sorry" in error_text.lower():
                print(f"Division {division_id} doesn't exist (got error page)")
                return False
        except:
            pass
        return False
    except Exception as e:
        print(f"Error checking division {division_id}: {e}")
        return False
    
def download_division(division_id, git_manager, driver):
    """Download data for a division that we know exists"""
    try:
        # Click the download button
        download_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "get-files"))
        )
        download_button.click()
        
        # Wait for and click the "Download as CSV" link
        csv_download = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Download as CSV"))
        )
        csv_download.click()
        
        # Wait a moment for the download to start
        time.sleep(2)
        
        # Increment download counter
        git_manager.download_count += 1
        
        # Every 25 downloads, commit and push to GitHub
        if git_manager.download_count % 25 == 0:
            git_manager.commit_and_push(division_id)
        
        return True
        
    except Exception as e:
        print(f"Error downloading division {division_id}: {e}")
        return False
        
chrome_options = uc.ChromeOptions()
download_dir = str(Path.cwd() / "parliament_divisions")
Path(download_dir).mkdir(exist_ok=True)

chrome_options.add_experimental_option('prefs', {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True
})

git_manager = GitManager(str(Path.cwd()))

def main():
    driver = uc.Chrome(options=chrome_options)
    start_id = 1
    end_id = 1926
    
    for division_id in tqdm(range(start_id, end_id + 1), desc="Processing divisions"):
        if check_division_exists(division_id, driver):
            success = download_division(division_id, git_manager, driver)
            if success:
                print(f"Successfully downloaded division {division_id}")
        time.sleep(2)
    
    git_manager.commit_and_push(end_id)
    driver.quit()

if __name__ == "__main__":
    main()