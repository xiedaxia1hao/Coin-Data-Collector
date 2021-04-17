from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pyvirtualdisplay import Display



display = Display(visible=0, size=(800, 600))
display.start()

chrome_options = Options()
#argument to switch off suid sandBox and no sandBox in Chrome 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-setuid-sandbox")

driver = webdriver.Chrome('/usr/bin/chromedriver_linux', chrome_options=chrome_options) 
driver.get('http://kean.edu')
print(driver.title)
driver.quit()

