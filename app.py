from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from GmailBox import GmailBox
import time, requests, os
from pyvirtualdisplay import Display
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
import pandas as pd
# Start a virtual display
display = Display(visible=0, size=(1920, 1080))
display.start()

postgres_engine = create_engine(os.getenv('POSTGRES_URL'), poolclass=NullPool)

Gmail = GmailBox()
New_Gmail = Gmail.new_email()
email = New_Gmail.email

username = f"{email.split("@")[0].replace(".","")}{int(time.time())}"

def wait_for_element(driver, xpath, waitS = 100):
    for i in range(waitS):
        if len(driver.find_elements(By.XPATH, xpath)) > 0:
            break
        time.sleep(1)
    else:
        raise Exception(f"Unable to locate element : {xpath}")

options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_extension("capsolver.crx")

driver = webdriver.Chrome(options)
driver.maximize_window()
driver.get("chrome-extension://hlifkpholllijblknnmbfagnkjneagid/popup/popup.html")
driver.get("https://huggingface.co/join")
print("Home Page loaded")
wait_for_element(driver, "//input[@name='email']")
driver.find_element(By.XPATH, "//input[@name='email']").send_keys(email)
driver.find_element(By.XPATH, "//input[@name='password']").send_keys(os.getenv("PASSWORD"))
wait_for_element(driver, "//input[@name='password']")
driver.find_element(By.XPATH, "//input[@name='password']").submit()
print("Filled email and pass and submit")
wait_for_element(driver, "//input[@name='username']")
driver.find_element(By.XPATH, "//input[@name='username']").send_keys(username)
driver.find_element(By.XPATH, "//input[@name='fullname']").send_keys("IMDB")
driver.find_element(By.XPATH, "//input[@type='checkbox']").click()
wait_for_element(driver, "//button[@type='submit']")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
driver.find_element(By.XPATH, "//button[text()='Skip']").click()
print("Waiting for email", email, username)

for i in range(60):
    inbox = Gmail.inbox(email)
    if inbox:
        conf_url = inbox[0].message.split("\n")[1].split("\n")[0]
        break
    else:
        time.sleep(1)
else:
    raise Exception("Email not received")

res = requests.get(conf_url)
driver.get("https://huggingface.co/settings/tokens")
driver.find_element(By.XPATH, "//form[@action='/settings/tokens/new']").click()
driver.find_element(By.XPATH, "//input[@name='displayName']").send_keys("imdb")
driver.find_element(By.XPATH, "(//div[@class='flex flex-col gap-2']//input[@value='repo.write'])[1]").click()
create_token_ele = driver.find_element(By.XPATH, "//button[text()='Create token']")
actions = ActionChains(driver)
actions.move_to_element(create_token_ele).perform()
create_token_ele.click()
print("Create token clicked")
wait_for_element(driver, "//div[@class='flex gap-2 max-sm:flex-col']/input")
el = driver.find_element(By.XPATH, "//div[@class='flex gap-2 max-sm:flex-col']/input")
hf_token = el.get_attribute("value")
data = {"email" : email, "username" : username, "hf_token" : hf_token}
df = pd.DataFrame([data])
df.to_sql(name='hfaccounts', con=postgres_engine, if_exists='append', index=False)
driver.quit()
print(data)