"""Pulls the results of loto page then calls parser."""
#!/usr/bin/env python3

from selenium.common.exceptions import TimeoutException

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from webdriver_manager.chrome import ChromeDriverManager

from results_parser import parse_results_page

# (0) Constants.
MAX_ATTEMPTS = 5
TIMEOUT = 14
OUTPUT_FOLDER_HTML = 'output/html'
OUTPUT_FOLDER_CSV = 'output/csv'

class Crawler():
    """Crawler for loto results page."""

    browser: Chrome
    url: str

    def __init__(self, url: str):
        # (1) Configure how chrome browser should be launched.
        options = Options()

        # Disable bloatware.
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        # Start maximized.
        options.add_argument("--start-maximized")
        # Start headless.
        options.add_argument("--headless")
        # Docker compatibility.
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # (2) Create the webdriver object. The first argument is chromedriver path, then options.
        # To resolve the chromedriver path we use the webdriver_manager package.
        # Because the class constructor contains other possible arguments between the chromedriver
        # path and options, we have to use a keyword argument.
        # Ref: https://docs.python.org/3/glossary.html#term-argument
        service = Service(ChromeDriverManager().install())
        self.browser = Chrome(
            service=service,
            options=options
        )

        self.url = url

    def parse_results(self):
        """Download the HTML page of each loto results, then parse it to CSV."""
        # (3) Crawling
        # (3.1) Launch browser then navigate to loto homepage.
        html_results = []
        self.browser.get(self.url)

        # (3.2) Locate the button to check results for each loto.
        elements = self.browser.find_elements(By.LINK_TEXT, 'Confira o resultado ›')

        # (3.3) For each element, click, locate the full results link.
        for element in elements:
            # (3.3.1) Open element in a new tab.
            main_handle = self.browser.current_window_handle
            self.browser.execute_script("window.open(arguments[0])", element.get_attribute('href'))
            self.browser.switch_to.window(
                self.browser.window_handles[len(self.browser.window_handles) - 1]
            )

            # (3.3.2) Wait for the page to load, fetch loto title.
            WebDriverWait(self.browser, TIMEOUT).until(
                expected_conditions.presence_of_element_located(
                    (By.PARTIAL_LINK_TEXT, ' por ordem crescente.')
                )
            )

            element = self.browser.find_element(By.PARTIAL_LINK_TEXT, ' por ordem crescente.')
            lototitle = self.browser.find_element(By.ID, 'tituloModalidade').text
            loto_window_handle = self.browser.current_window_handle

            # (3.3.3) Open the results (which are open in a new tab).
            self.browser.execute_script('arguments[0].click()', element)
            self.browser.switch_to.window(
                self.browser.window_handles[len(self.browser.window_handles) - 1]
            )
            self.browser.refresh()

            attempts = MAX_ATTEMPTS
            while attempts > 0:
                try:
                    WebDriverWait(self.browser, TIMEOUT).until(
                        expected_conditions.presence_of_element_located((By.TAG_NAME, 'table'))
                    )
                    break
                except TimeoutException:
                    print(f'Attempt {attempts} for {lototitle}, waited for {TIMEOUT} seconds.')
                    self.browser.refresh()
                attempts -= 1
            if attempts == 0 and len(self.browser.find_elements(By.TAG_NAME, 'table')) == 0:
                print(f'Failed to load results for {lototitle}')
            else:
                # (3.3.4) Download the HTML.
                html_results.append(f'resultados_{lototitle}.html')
                filename = f'{OUTPUT_FOLDER_HTML}/{html_results[len(html_results) - 1]}'
                with open(filename, "w", encoding='UTF-8') as file_descriptor:
                    file_descriptor.write(self.browser.page_source)

            # (3.3.5) Close results tab.
            self.browser.close()

            # (3.3.6) Close loto tab.
            self.browser.switch_to.window(loto_window_handle)
            self.browser.close()

            # (3.3.7) Navigate back to main page.
            self.browser.switch_to.window(main_handle)

        # (3.4) Clean-up then finish.
        self.browser.delete_all_cookies()
        self.browser.quit()

        # (4) Parsing results.
        for html_result in html_results:
            filename = f'{OUTPUT_FOLDER_HTML}/{html_result}'
            csv_contents = ''
            with open(filename, 'r', encoding='UTF-8') as file_descriptor:
                csv_contents = parse_results_page(file_descriptor.read())
            csv_result = html_result.rstrip('.html') + '.csv'
            csv_result = csv_result.lower().replace(' ', '_').replace('+', '').replace('á', 'a')
            filename = f'{OUTPUT_FOLDER_CSV}/{csv_result}'
            with open(filename, 'w', encoding='UTF-8') as file_descriptor:
                file_descriptor.write(csv_contents)

# (5) Executing the code.
crawler = Crawler('https://loterias.caixa.gov.br/Paginas/default.aspx')
crawler.parse_results()
