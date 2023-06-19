#!/usr/bin/env python3
from time import sleep

from results_parser import parse_results_page

from selenium.common.exceptions import TimeoutException

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from webdriver_manager.chrome import ChromeDriverManager

# (0) Constants.
ATTEMPTS = 5
TIMEOUT = 14
OUTPUT_FOLDER_HTML = 'output/html'
OUTPUT_FOLDER_CSV = 'output/csv'

# (1) Configure how chrome browser should be launched.
options = Options()

# Disable bloatware.
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
# Start maximized.
options.add_argument("--start-maximized")
# Start headless.
#options.add_argument("--headless")

# (2) Create the webdriver object. The first argument is chromedriver path, then options.
# To resolve the chromedriver path we use the webdriver_manager package.
# Because the class constructor contains other possible arguments between the chromedriver
# path and options, we have to use a keyword argument (https://docs.python.org/3/glossary.html#term-argument).
service = Service(ChromeDriverManager().install())
browser = Chrome(
    service=service,
    options=options
)

# (3) Crawling
# (3.1) Launch browser then navigate to loto homepage.
html_results = []
browser.get('https://loterias.caixa.gov.br/Paginas/default.aspx')

# (3.2) Locate the button to check results for each loto.
elements = browser.find_elements(By.LINK_TEXT, 'Confira o resultado ›')

# (3.3) For each element, click, locate the full results link.
for element in elements:
    # (3.3.1) Open element in a new tab.
    main_handle = browser.current_window_handle
    browser.execute_script("window.open(arguments[0])", element.get_attribute('href'))
    browser.switch_to.window(browser.window_handles[len(browser.window_handles) - 1])

    # (3.3.2) Wait for the page to load, fetch loto title.
    WebDriverWait(browser, TIMEOUT).until(
        expected_conditions.presence_of_element_located((By.PARTIAL_LINK_TEXT, ' por ordem crescente.'))
    )    
    element = browser.find_element(By.PARTIAL_LINK_TEXT, ' por ordem crescente.')
    lototitle = browser.find_element(By.ID, 'tituloModalidade').text
    loto_window_handle = browser.current_window_handle

    # (3.3.3) Open the results (which are open in a new tab).
    browser.execute_script('arguments[0].click()', element)
    browser.switch_to.window(browser.window_handles[len(browser.window_handles) - 1])
    browser.refresh()

    attempts = ATTEMPTS
    while attempts > 0:
        try:
            WebDriverWait(browser, TIMEOUT).until(
                expected_conditions.presence_of_element_located((By.TAG_NAME, 'table'))
            )
            break
        except TimeoutException:
            print('Attempt {} for {}, waited for {} seconds. Refreshing the page'.format(attempts, lototitle, TIMEOUT))
            browser.refresh()
        attempts -= 1
    
    if attempts == 0 and len(browser.find_elements(By.TAG_NAME, 'table')) == 0:
        print('Failed to load results for {}'.format(lototitle))
    else:
        # (3.3.4) Download the HTML.
        html_results.append('resultados_{}.html'.format(lototitle))
        with open('{}/{}'.format(OUTPUT_FOLDER_HTML, html_results[len(html_results) - 1]), "w") as fd:
            fd.write(browser.page_source)

    # (3.3.5) Close results tab.
    browser.close()

    # (3.3.6) Close loto tab.
    browser.switch_to.window(loto_window_handle)
    browser.close()

    # (3.3.7) Navigate back to main page.
    browser.switch_to.window(main_handle)

# (3.4) Clean-up then finish.
browser.delete_all_cookies()
browser.quit()

# 4 Parsing Results
for html_result in html_results:
    csv_contents = ''
    with open('{}/{}'.format(OUTPUT_FOLDER_HTML, html_result)) as fd:
        csv_contents = parse_results_page(fd.read())
    
    csv_result = '{}.csv'.format(html_result.rstrip('.html'))
    with open('{}/{}'.format(OUTPUT_FOLDER_CSV, csv_result), 'w') as fd:
        fd.write(csv_contents)