import requests
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pickle
import time
import json
import hashlib
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from selenium.webdriver.support.ui import WebDriverWait


DEFAULT_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'

def filesize(fn):
    if os.path.exists(fn):
        return os.path.getsize(fn)
    return 0

def loadjson(fn):
	fh=open(fn,'r')
	jj=json.load(fh)
	fh.close()
	return jj

def loaddom(fn):
	return BeautifulSoup(open(fn), 'html.parser')

def md5(str):
	return hashlib.md5(str.encode('utf-8')).hexdigest()


def get_clear_browsing_button(driver):
    """Find the "CLEAR BROWSING BUTTON" on the Chrome settings page."""
    return driver.find_element_by_id('* /deep/ #clearBrowsingDataConfirm')
	
def clear_cache(driver, timeout=60):
    """Clear the cookies and cache for the ChromeDriver instance."""
    # navigate to the settings page
    driver.get('chrome://settings/clearBrowserData')

    # wait for the button to appear
    wait = WebDriverWait(driver, timeout)
    wait.until(get_clear_browsing_button)

    # click the button to clear the cache
    get_clear_browsing_button(driver).click()

    # wait for the button to be gone before returning
    wait.until_not(get_clear_browsing_button)

class MyRequest:
	headers = {
		'user-agent': DEFAULT_UA
	}
	_session = None

	def __init__(self, start_page, cookie_fn, headless = True, userdir = ''):
		cookies = None
		if os.path.exists(cookie_fn):
			print('Loading cookies...')
			cookies = pickle.load(open(cookie_fn, "rb"))
		else:
			print('Initializing cookies...')
			chrome_options = Options()
			if headless:
				chrome_options.add_argument("--headless")
			# in Mac: d=util.MyChrome(False,'/Users/yu/Library/Application Support/Google/Chrome')
			if userdir != '':
				chrome_options.add_argument(f'user-data-dir={userdir}')
			#chrome_options.add_argument("--headless")
			chrome_options.add_argument(f'user-agent={DEFAULT_UA}')
			chrome_options.add_argument("--window-size=1920x1080")
    		# required by running as root
			chrome_options.add_argument("--no-sandbox")
			driver = webdriver.Chrome(chrome_options=chrome_options)
			driver.get(start_page)
			cookies = driver.get_cookies()
			pickle.dump(driver.get_cookies(), open(cookie_fn, "wb"))
			driver.close()
		if cookies is None:
			print('Unknown error: failed to initialize cookies')
		if self._session is None:
			self._session = requests.Session()
		for cookie in cookies:
			self._session.cookies.set(cookie['name'], cookie['value'])


	def get(self, url, dom = True):	
		raw = self._session.get(url, headers=self.headers)
		raw.encoding = 'utf-8'
		if dom:
			dom = BeautifulSoup(raw.text, 'html.parser')
			return dom
		return raw.text
	
	def getp(self, url, paras, dom = True):	
		raw = self._session.get(url, headers=self.headers, params = paras)
		raw.encoding = 'utf-8'
		if dom:
			dom = BeautifulSoup(raw.text, 'html.parser')
			return dom
		return raw.text
	
	def save(self, url, fn, paras = None):
		if paras is None:
			raw = self._session.get(url, headers = self.headers)
		else:
			raw = self._session.get(url, headers = self.headers, params = paras)
		outf = open(fn, 'w', encoding='utf-8')
		raw.encoding = 'utf-8'
		outf.write(raw.text)
		outf.close()
		return len(raw.text)

# smart class
class MyChrome:
	headers = {
		'user-agent': DEFAULT_UA
	}
	_driver = None

	def __init__(self, headless = True, userdir = ''):
		chrome_options = Options()
		if headless:
			chrome_options.add_argument("--headless")
		# in Mac: d=util.MyChrome(False,'/Users/yu/Library/Application Support/Google/Chrome')
		if userdir != '':
			chrome_options.add_argument(f'user-data-dir={userdir}')
		ua = generate_user_agent()
		chrome_options.add_argument(f'user-agent={ua}')
		chrome_options.add_argument("--window-size=1920x1080")
		# required by running as root
		chrome_options.add_argument("--no-sandbox")
		self._driver = webdriver.Chrome(chrome_options=chrome_options)
	
	def goto(self, url):
		self._driver.get(url)

	def clear(self):
		clear_cache(self._driver)

	def smart_wait(self, element_xpath_or_id, element_desc = None):  # 智能等待时间，60秒超时
		if element_desc is None:
			element_desc = element_xpath_or_id
		find_func = self._driver.find_element_by_name
		find_para = element_xpath_or_id
		if element_xpath_or_id.startswith('#'):
			find_func = self._driver.find_element_by_id  # we also support id
			find_para = element_xpath_or_id[1:]
		elif element_xpath_or_id.startswith('/'):
			find_func = self._driver.find_element_by_xpath
		elif element_xpath_or_id.find('.') != -1:
			find_func = self._driver.find_element_by_css_selector
		for i in range(60):            # 循环60次，从0至59
			if i >= 59 :               # 当i大于等于59时，打印提示时间超时
				print(element_desc, "timeout")
				print(self._driver.page_source)
				break
			try:
				element = find_func(find_para)                     # try代码块中出现找不到特定元素的异常会执行except中的代码
				if element: # 如果能查找到特定的元素id就提前退出循环
					return element
			except:                    # 上面try代码块中出现异常，except中的代码会执行打印提示会继续尝试查找特定的元素id
				print("wait for ", element_desc, i)
			time.sleep(1)
		return None
	
	def smart_find(self, element_xpath_or_id):
		find_func = self._driver.find_element_by_name
		find_para = element_xpath_or_id
		if element_xpath_or_id.startswith('#'):
			find_func = self._driver.find_element_by_id  # we also support id
			find_para = element_xpath_or_id[1:]
		elif element_xpath_or_id.startswith('/'):
			find_func = self._driver.find_element_by_xpath
		elif element_xpath_or_id.find('.') != -1:
			find_func = self._driver.find_element_by_css_selector
		try:
			element = find_func(find_para)                     # try代码块中出现找不到特定元素的异常会执行except中的代码
			if element: # 如果能查找到特定的元素id就提前退出循环
				return element
		except:                    # 上面try代码块中出现异常，except中的代码会执行打印提示会继续尝试查找特定的元素id
			print('not found')
		return None

	def infinite_scroll(self,SCROLL_PAUSE_TIME = 1):
		# Get scroll height
		last_height = self._driver.execute_script("return document.body.scrollHeight")
		while True:
			# Scroll down to bottom
			self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			# Wait to load page
			time.sleep(SCROLL_PAUSE_TIME)
			# Calculate new scroll height and compare with last scroll height
			new_height = self._driver.execute_script("return document.body.scrollHeight")
			if new_height == last_height:
				break
			last_height = new_height

	# prevent chrome halt after long time operation
	def reset(self):
		self.close()
		self.__init__()

	def close(self):
		if self._driver is not None:
			self._driver.close()