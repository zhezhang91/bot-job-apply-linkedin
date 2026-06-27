'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

Support me: https://github.com/sponsors/GodsScion

version:    26.01.20.5.08
'''


# Imports
import os
import csv
import re
import time
import shutil
import pyautogui

# Set CSV field size limit to prevent field size errors
csv.field_size_limit(1000000)  # Set to 1MB instead of default 131KB


def _ensure_private_config() -> None:
    '''Create personals.py / secrets.py from examples when missing (not stored in git).'''
    for example, target in [
        ("config/personals.example.py", "config/personals.py"),
        ("config/secrets.example.py", "config/secrets.py"),
    ]:
        if os.path.exists(target):
            continue
        if os.path.exists(example):
            shutil.copy(example, target)
            print(f"Created {target} from example — please edit it with your details.")
        else:
            raise FileNotFoundError(
                f"Missing {target}. Copy config/{os.path.basename(example)} to {target} and fill in your details."
            )


_ensure_private_config()

from random import choice, shuffle, randint
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, NoSuchWindowException, ElementNotInteractableException, WebDriverException

from config.personals import *
from config.questions import *
from config.search import *
from config.secrets import use_AI, username, password, ai_provider
from config.settings import *

from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
from modules.validator import validate_config

if use_AI:
    from modules.ai.openaiConnections import ai_create_openai_client, ai_extract_skills, ai_answer_question, ai_close_openai_client
    from modules.ai.deepseekConnections import deepseek_create_client, deepseek_extract_skills, deepseek_answer_question
    from modules.ai.geminiConnections import gemini_create_client, gemini_extract_skills, gemini_answer_question

from typing import Literal


pyautogui.FAILSAFE = False
# if use_resume_generator:    from resume_generator import is_logged_in_GPT, login_GPT, open_resume_chat, create_custom_resume


#< Global Variables and logics

if run_in_background == True:
    pause_at_failed_question = False
    pause_before_submit = False
    run_non_stop = False

first_name = first_name.strip()
middle_name = middle_name.strip()
last_name = last_name.strip()
full_name = first_name + " " + middle_name + " " + last_name if middle_name else first_name + " " + last_name

useNewResume = True
randomly_answered_questions = set()

tabs_count = 1
easy_applied_count = 0
external_jobs_count = 0
bookmarked_count = 0
failed_count = 0
skip_count = 0
dailyEasyApplyLimitReached = False

re_experience = re.compile(r'[(]?\s*(\d+)\s*[)]?\s*[-to]*\s*\d*[+]*\s*year[s]?', re.IGNORECASE)

desired_salary_lakhs = str(round(desired_salary / 100000, 2))
desired_salary_monthly = str(round(desired_salary/12, 2))
desired_salary = str(desired_salary)

current_ctc_lakhs = str(round(current_ctc / 100000, 2))
current_ctc_monthly = str(round(current_ctc/12, 2))
current_ctc = str(current_ctc)

notice_period_months = str(notice_period//30)
notice_period_weeks = str(notice_period//7)
notice_period = str(notice_period)

aiClient = None
##> ------ Dheeraj Deshwal : dheeraj9811 Email:dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Feature ------
about_company_for_ai = None # TODO extract about company for AI
##<

#>


#< Login Functions
def is_logged_in_LN() -> bool:
    '''
    Function to check if user is logged-in in LinkedIn
    * Returns: `True` if user is logged-in or `False` if not
    '''
    if driver.current_url == "https://www.linkedin.com/feed/": return True
    if try_linkText(driver, "Sign in"): return False
    if try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]'):  return False
    if try_linkText(driver, "Join now"): return False
    print_lg("Didn't find Sign in link, so assuming user is logged in!")
    return True


def login_LN() -> None:
    '''
    Function to login for LinkedIn
    * Tries to login using given `username` and `password` from `secrets.py`
    * If failed, tries to login using saved LinkedIn profile button if available
    * If both failed, asks user to login manually
    '''
    # Find the username and password fields and fill them with user credentials
    driver.get("https://www.linkedin.com/login")
    if username == "username@example.com" and password == "example_password":
        print_lg("User did not configure username and password in secrets.py, hence can't login automatically! Please login manually!")
        manual_login_retry(is_logged_in_LN, 2)
        return
    try:
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Forgot password?")))
        try:
            text_input_by_ID(driver, "username", username, 1)
        except Exception as e:
            print_lg("Couldn't find username field.")
            # print_lg(e)
        try:
            text_input_by_ID(driver, "password", password, 1)
        except Exception as e:
            print_lg("Couldn't find password field.")
            # print_lg(e)
        # Find the login submit button and click it
        driver.find_element(By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]').click()
    except Exception as e1:
        try:
            profile_button = find_by_class(driver, "profile__details")
            profile_button.click()
        except Exception as e2:
            # print_lg(e1, e2)
            print_lg("Couldn't Login!")

    try:
        # Wait until successful redirect, indicating successful login
        wait.until(EC.url_to_be("https://www.linkedin.com/feed/")) # wait.until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space(.)="Start a post"]')))
        return print_lg("Login successful!")
    except Exception as e:
        print_lg("Seems like login attempt failed! Possibly due to wrong credentials or already logged in! Try logging in manually!")
        # print_lg(e)
        manual_login_retry(is_logged_in_LN, 2)
#>



def get_applied_job_ids() -> set[str]:
    '''
    Function to get a `set` of applied job's Job IDs
    * Returns a set of Job IDs from existing applied jobs history csv file
    '''
    job_ids: set[str] = set()
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                job_ids.add(row[0])
    except FileNotFoundError:
        print_lg(f"The CSV file '{file_name}' does not exist.")
    return job_ids



def get_saved_job_ids() -> set[str]:
    '''
    Function to get a set of job IDs already bookmarked in the saved jobs CSV.
    '''
    job_ids: set[str] = set()
    try:
        with open(saved_jobs_file_name, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    job_ids.add(row[0])
    except FileNotFoundError:
        print_lg(f"The CSV file '{saved_jobs_file_name}' does not exist.")
    return job_ids


def save_job_on_linkedin(job_card: WebElement | None = None) -> tuple[bool, str]:
    '''
    Clicks LinkedIn Save on the job details panel (or job list card as fallback).
    '''
    def _click_save_button(btn: WebElement) -> bool:
        scroll_to_view(driver, btn)
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable(btn))
            btn.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            driver.execute_script("arguments[0].click();", btn)
        buffer(click_gap)
        return True

    def _try_buttons(buttons: list[WebElement]) -> tuple[bool, str] | None:
        for btn in buttons:
            try:
                if not btn.is_displayed():
                    continue
                aria = (btn.get_attribute("aria-label") or "").strip().lower()
                if "unsave" in aria or aria.startswith("saved"):
                    return True, "Already saved on LinkedIn"
                if "save" in aria:
                    _click_save_button(btn)
                    return True, "Saved on LinkedIn"
            except Exception:
                continue
        return None

    try:
        # Wait for the right-hand job details pane to finish loading after card click.
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-details, .jobs-search__job-details, .jobs-unified-top-card"))
            )
        except Exception:
            pass

        # Scroll details panel back to top — description reading scrolls away from the Save button.
        for panel_selector in [".jobs-search__job-details", ".jobs-details", ".scaffold-layout__detail"]:
            try:
                panel = driver.find_element(By.CSS_SELECTOR, panel_selector)
                driver.execute_script("arguments[0].scrollTop = 0;", panel)
                break
            except Exception:
                continue

        detail_scopes: list[WebElement] = []
        for scope_selector in [
            (By.CLASS_NAME, "jobs-details"),
            (By.CLASS_NAME, "jobs-search__job-details"),
            (By.CSS_SELECTOR, ".jobs-unified-top-card"),
            (By.CSS_SELECTOR, ".job-details-jobs-unified-top-card"),
        ]:
            try:
                detail_scopes.append(driver.find_element(*scope_selector))
            except Exception:
                continue

        detail_selectors = [
            (By.CSS_SELECTOR, "button.jobs-save-button"),
            (By.CSS_SELECTOR, "button[class*='jobs-save-button']"),
            (By.CSS_SELECTOR, "button[aria-label*='Save job']"),
            (By.CSS_SELECTOR, "button[aria-label*='Save Job']"),
            (By.CSS_SELECTOR, "button[aria-label*='Unsave job']"),
            (By.CSS_SELECTOR, "button[aria-label*='Unsave Job']"),
            (By.CSS_SELECTOR, "[data-control-name='save_job']"),
            (By.CSS_SELECTOR, "[data-control-name='save_application_btn']"),
            (By.XPATH, ".//button[contains(@class,'jobs-save-button')]"),
            (By.XPATH, ".//button[contains(@aria-label,'Save')]"),
        ]

        for scope in detail_scopes:
            for by, selector in detail_selectors:
                try:
                    result = _try_buttons(scope.find_elements(by, selector))
                    if result:
                        return result
                except Exception:
                    continue

        # Explicit wait — LinkedIn sometimes renders the save button slightly late.
        for scope in detail_scopes or [driver]:
            try:
                btn = WebDriverWait(scope, 6).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.jobs-save-button, button[class*='jobs-save-button']"))
                )
                aria = (btn.get_attribute("aria-label") or "").strip().lower()
                if "unsave" in aria or aria.startswith("saved"):
                    return True, "Already saved on LinkedIn"
                _click_save_button(btn)
                return True, "Saved on LinkedIn"
            except Exception:
                continue

        # Fallback: save icon on the job card in the left list (visible without details pane).
        if job_card:
            card_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Save job']"),
                (By.CSS_SELECTOR, "button[aria-label*='Save Job']"),
                (By.CSS_SELECTOR, "button[aria-label*='Unsave job']"),
                (By.CSS_SELECTOR, "button.job-card-container__action"),
                (By.XPATH, ".//button[contains(@class,'job-card-container__action')]"),
                (By.XPATH, ".//button[contains(@aria-label,'Save')]"),
            ]
            for by, selector in card_selectors:
                try:
                    result = _try_buttons(job_card.find_elements(by, selector))
                    if result:
                        return result
                except Exception:
                    continue

        return False, "Save button not found"
    except Exception as e:
        return False, str(e)


def record_saved_job(job_id: str, title: str, company: str, work_location: str, work_style: str, job_link: str, status: str) -> None:
    try:
        with open(saved_jobs_file_name, mode='a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 'Date Saved', 'Job Link', 'Status']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if csv_file.tell() == 0:
                writer.writeheader()
            writer.writerow({
                'Job ID': truncate_for_csv(job_id),
                'Title': truncate_for_csv(title),
                'Company': truncate_for_csv(company),
                'Work Location': truncate_for_csv(work_location),
                'Work Style': truncate_for_csv(work_style),
                'Date Saved': datetime.now(),
                'Job Link': truncate_for_csv(job_link),
                'Status': truncate_for_csv(status),
            })
    except Exception as e:
        print_lg("Failed to update saved jobs list!", e)


def set_search_location() -> None:
    '''
    Function to set search location
    '''
    if search_location.strip():
        try:
            print_lg(f'Setting search location as: "{search_location.strip()}"')
            search_location_ele = try_xp(driver, ".//input[@aria-label='City, state, or zip code'and not(@disabled)]", False) #  and not(@aria-hidden='true')]")
            text_input(actions, search_location_ele, search_location, "Search Location")
        except ElementNotInteractableException:
            try_xp(driver, ".//label[@class='jobs-search-box__input-icon jobs-search-box__keywords-label']")
            actions.send_keys(Keys.TAB, Keys.TAB).perform()
            actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            actions.send_keys(search_location.strip()).perform()
            sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            try_xp(driver, ".//button[@aria-label='Cancel']")
        except Exception as e:
            try_xp(driver, ".//button[@aria-label='Cancel']")
            print_lg("Failed to update search location, continuing with default location!", e)


def apply_filters() -> None:
    '''
    Function to apply job search filters
    '''
    set_search_location()

    try:
        recommended_wait = 1 if click_gap < 1 else 0

        wait.until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space()="All filters"]'))).click()
        buffer(recommended_wait)

        wait_span_click(driver, sort_by)
        wait_span_click(driver, date_posted)
        buffer(recommended_wait)

        multi_sel_noWait(driver, experience_level) 
        multi_sel_noWait(driver, companies, actions)
        if experience_level or companies: buffer(recommended_wait)

        multi_sel_noWait(driver, job_type)
        multi_sel_noWait(driver, on_site)
        if job_type or on_site: buffer(recommended_wait)

        if easy_apply_only: boolean_button_click(driver, actions, "Easy Apply")
        
        multi_sel_noWait(driver, location)
        multi_sel_noWait(driver, industry)
        if location or industry: buffer(recommended_wait)

        multi_sel_noWait(driver, job_function)
        multi_sel_noWait(driver, job_titles)
        if job_function or job_titles: buffer(recommended_wait)

        if under_10_applicants: boolean_button_click(driver, actions, "Under 10 applicants")
        if in_your_network: boolean_button_click(driver, actions, "In your network")
        if fair_chance_employer: boolean_button_click(driver, actions, "Fair Chance Employer")

        wait_span_click(driver, salary)
        buffer(recommended_wait)
        
        multi_sel_noWait(driver, benefits)
        multi_sel_noWait(driver, commitments)
        if benefits or commitments: buffer(recommended_wait)

        show_results_button: WebElement = driver.find_element(By.XPATH, '//button[contains(translate(@aria-label, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "apply current filters to show")]')
        show_results_button.click()

        global pause_after_filters
        if pause_after_filters and "Turn off Pause after search" == pyautogui.confirm("These are your configured search results and filter. It is safe to change them while this dialog is open, any changes later could result in errors and skipping this search run.", "Please check your results", ["Turn off Pause after search", "Look's good, Continue"]):
            pause_after_filters = False

    except Exception as e:
        print_lg("Setting the preferences failed!", e)
        # print_lg(e)



def get_page_info() -> tuple[WebElement | None, int | None]:
    '''
    Function to get pagination element and current page number
    '''
    try:
        pagination_element = try_find_by_classes(driver, ["jobs-search-pagination__pages", "artdeco-pagination", "artdeco-pagination__pages"])
        scroll_to_view(driver, pagination_element)
        current_page = int(pagination_element.find_element(By.XPATH, "//button[contains(@class, 'active')]").text)
    except Exception as e:
        print_lg("Failed to find Pagination element, hence couldn't scroll till end!")
        pagination_element = None
        current_page = None
        print_lg(e)
    return pagination_element, current_page



JOB_LISTING_XPATHS = [
    "//li[@data-occludable-job-id]",
    "//li[contains(@class,'jobs-saved-jobs-list__list-item')]",
    "//li[contains(@class,'jobs-collection-list__item')]",
    "//li[contains(@class,'scaffold-layout__list-item') and .//a[contains(@href,'/jobs/view/')]]",
    "//div[contains(@class,'job-card-container') and .//a[contains(@href,'/jobs/view/')]]",
]

SAVED_JOBS_URL_FALLBACKS = [
    "https://www.linkedin.com/jobs/collections/saved/",
    "https://www.linkedin.com/my-items/saved-jobs/",
]


def extract_job_id_from_element(job: WebElement) -> str:
    for attr in ('data-occludable-job-id', 'data-job-id'):
        value = (job.get_dom_attribute(attr) or "").strip()
        if value:
            return value
    urn = job.get_dom_attribute('data-entity-urn') or ""
    if urn:
        match = re.search(r'jobPosting:(\d+)', urn)
        if match:
            return match.group(1)
    for anchor in job.find_elements(By.XPATH, ".//a[contains(@href,'/jobs/view/') or contains(@href,'currentJobId=')]"):
        href = anchor.get_attribute('href') or ''
        match = re.search(r'/jobs/view/(\d+)', href) or re.search(r'currentJobId=(\d+)', href)
        if match:
            return match.group(1)
    return ""


def wait_for_job_listings(timeout: float = 12) -> str | None:
    for xpath in JOB_LISTING_XPATHS:
        try:
            WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
            if driver.find_elements(By.XPATH, xpath):
                return xpath
        except Exception:
            continue
    return None


def get_job_listings(active_xpath: str | None = None) -> list[WebElement]:
    if active_xpath:
        listings = driver.find_elements(By.XPATH, active_xpath)
        if listings:
            return listings
    for xpath in JOB_LISTING_XPATHS:
        listings = driver.find_elements(By.XPATH, xpath)
        if listings:
            return listings
    return []


def find_job_card_by_id(job_id: str) -> WebElement | None:
    xpaths = [
        f"//li[@data-occludable-job-id='{job_id}']",
        f"//li[contains(@class,'jobs-saved-jobs-list__list-item') and .//a[contains(@href,'/jobs/view/{job_id}')]]",
        f"//a[contains(@href,'/jobs/view/{job_id}')]/ancestor::li[1]",
        f"//a[contains(@href,'/jobs/view/{job_id}')]/ancestor::div[contains(@class,'job-card-container')][1]",
    ]
    for xpath in xpaths:
        try:
            return driver.find_element(By.XPATH, xpath)
        except Exception:
            continue
    return None


def open_saved_jobs_page() -> str | None:
    saved_urls: list[str] = []
    for url in [saved_jobs_url, *SAVED_JOBS_URL_FALLBACKS]:
        if url not in saved_urls:
            saved_urls.append(url)
    for url in saved_urls:
        driver.get(url)
        buffer(4)
        active_xpath = wait_for_job_listings(15)
        if active_xpath:
            print_lg(f'Loaded Saved jobs from: {url}')
            return active_xpath
    return None


def parse_job_card_details(job: WebElement) -> tuple[str, str, str]:
    '''
    Returns company, work_location, and work_style from a job list card.
    '''
    company, work_location, work_style = "", "", ""
    try:
        subtitle = job.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle').text.strip()
        company, work_location = subtitle, ""
        for sep in [' · ', ' • ', ' | ']:
            if sep in subtitle:
                company, work_location = [part.strip() for part in subtitle.split(sep, 1)]
                break
        if not work_location:
            try:
                work_location = job.find_element(By.CLASS_NAME, 'job-card-container__metadata-item').text.strip()
            except Exception:
                work_location = ""
    except Exception:
        lines = [line.strip() for line in job.text.split('\n') if line.strip()]
        if len(lines) > 1:
            company = lines[1]
        if len(lines) > 2:
            work_location = lines[2]
    if work_location and '(' in work_location and ')' in work_location:
        work_style = work_location[work_location.rfind('(')+1:work_location.rfind(')')]
        work_location = work_location[:work_location.rfind('(')].strip()
    return company, work_location, work_style


def extract_work_location_from_top_card(jobs_top_card: WebElement) -> tuple[str, str]:
    '''
    Reads the more accurate location shown on the job details panel.
    '''
    work_location, work_style = "", ""
    try:
        for text in [span.text.strip() for span in jobs_top_card.find_elements(By.XPATH, './/span[contains(@class,"tvm__text")]') if span.text.strip()]:
            lower = text.lower()
            if lower in ['remote', 'hybrid', 'on-site', 'onsite']:
                work_style = text
            elif 'ago' not in lower and 'applicant' not in lower and 'promoted' not in lower:
                if not work_location:
                    work_location = text
    except Exception as e:
        print_lg("Failed to extract location from job details!", e)
    return work_location, work_style


def extract_company_size(*texts: str) -> int | None:
    combined = " ".join(text for text in texts if text).lower()
    range_match = re.search(r'(\d[\d,]*)\s*-\s*(\d[\d,]*)\s*employees', combined)
    if range_match:
        return int(range_match.group(2).replace(',', ''))
    plus_match = re.search(r'(\d[\d,]*)\+\s*employees', combined)
    if plus_match:
        return int(plus_match.group(1).replace(',', ''))
    count_match = re.search(r'(\d[\d,]*)\s*employees', combined)
    if count_match:
        return int(count_match.group(1).replace(',', ''))
    return None


def should_skip_for_title(title: str) -> tuple[bool, str]:
    title_lower = title.lower()
    if blocked_job_title_keywords and any(keyword.lower() in title_lower for keyword in blocked_job_title_keywords):
        return True, f'Title "{title}" matches a blocked title keyword'
    if allowed_job_title_keywords and not any(keyword.lower() in title_lower for keyword in allowed_job_title_keywords):
        return True, f'Title "{title}" does not match allowed job title keywords'
    return False, ""


def should_skip_for_company_name(company: str) -> tuple[bool, str]:
    company_lower = company.lower()
    if blocked_company_name_keywords and any(keyword.lower() in company_lower for keyword in blocked_company_name_keywords):
        return True, f'Company "{company}" matches a blocked company keyword'
    return False, ""


def should_skip_for_company_size(about_company_text: str, jobs_top_card: WebElement | None = None) -> tuple[bool, str, int | None]:
    if min_company_size <= 0 and max_company_size <= 0:
        return False, "", None
    top_card_text = jobs_top_card.text if jobs_top_card else ""
    company_size = extract_company_size(about_company_text, top_card_text)
    if company_size is None:
        if skip_unknown_company_size:
            return True, "Company size could not be detected", None
        return False, "", None
    if min_company_size > 0 and company_size < min_company_size:
        return True, f'Company size {company_size:,} employees is below minimum {min_company_size:,}', company_size
    if max_company_size > 0 and company_size > max_company_size:
        return True, f'Company size {company_size:,} employees is above maximum {max_company_size:,}', company_size
    return False, "", company_size


def should_skip_for_location(work_location: str, work_style: str) -> tuple[bool, str]:
    location_text = f"{work_location} {work_style}".strip().lower()
    if not location_text:
        return False, ""
    if blocked_locations and any(loc.lower() in location_text for loc in blocked_locations):
        return True, f'Location "{work_location or work_style}" is in blocked locations'
    allowed = allowed_locations + allowed_metro_locations
    if not allowed:
        return False, ""
    if any(loc.lower() in location_text for loc in allowed):
        return False, ""
    if allow_remote_canada and 'canada' in location_text and not any(loc.lower() in location_text for loc in blocked_locations):
        if 'remote' in location_text or 'remote' in work_style.lower() or 'hybrid' in work_style.lower():
            return False, ""
    if 'remote' in location_text or 'remote' in work_style.lower():
        return False, ""
    return True, f'Location "{work_location or work_style}" not in allowed locations'


def get_job_main_details(job: WebElement, blacklisted_companies: set, rejected_jobs: set, use_search_filters: bool = True) -> tuple[str, str, str, str, str, bool]:
    '''
    # Function to get job main details.
    Returns a tuple of (job_id, title, company, work_location, work_style, skip)
    * job_id: Job ID
    * title: Job title
    * company: Company name
    * work_location: Work location of this job
    * work_style: Work style of this job (Remote, On-site, Hybrid)
    * skip: A boolean flag to skip this job
    '''
    skip = False
    job_details_button = None
    for anchor in job.find_elements(By.TAG_NAME, 'a'):
        href = anchor.get_attribute('href') or ''
        if '/jobs/view/' in href or 'currentJobId=' in href:
            job_details_button = anchor
            break
    if not job_details_button:
        job_details_button = job.find_element(By.TAG_NAME, 'a')
    scroll_to_view(driver, job_details_button, True)
    job_id = extract_job_id_from_element(job)
    if not job_id:
        print_lg('Could not read job ID from listing, skipping this card.')
        return ("", job_details_button.text.split('\n')[0] if job_details_button.text else "Unknown", "", "", "", True)
    title = job_details_button.text
    title = title[:title.find("\n")] if "\n" in title else title
    company, work_location, work_style = parse_job_card_details(job)
    
    if use_search_filters:
        skip_for_title, title_reason = should_skip_for_title(title)
        if skip_for_title:
            print_lg(f'Skipping "{title} | {company}" job ({title_reason}). Job ID: {job_id}!')
            skip = True
        skip_for_company_name, company_reason = should_skip_for_company_name(company)
        if not skip and skip_for_company_name:
            print_lg(f'Skipping "{title} | {company}" job ({company_reason}). Job ID: {job_id}!')
            skip = True
    
    # Skip if previously rejected due to blacklist or already applied
    if company in blacklisted_companies:
        print_lg(f'Skipping "{title} | {company}" job (Blacklisted Company). Job ID: {job_id}!')
        skip = True
    elif job_id in rejected_jobs: 
        print_lg(f'Skipping previously rejected "{title} | {company}" job. Job ID: {job_id}!')
        skip = True
    try:
        if job.find_element(By.CLASS_NAME, "job-card-container__footer-job-state").text == "Applied":
            skip = True
            print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
    except: pass
    try: 
        if not skip: job_details_button.click()
    except Exception as e:
        print_lg(f'Failed to click "{title} | {company}" job on details button. Job ID: {job_id}!') 
        # print_lg(e)
        discard_job()
        job_details_button.click() # To pass the error outside
    buffer(click_gap)
    return (job_id,title,company,work_location,work_style,skip)


# Function to check for Blacklisted words in About Company
def check_blacklist(rejected_jobs: set, job_id: str, company: str, blacklisted_companies: set) -> tuple[set, set, WebElement, str]:
    jobs_top_card = try_find_by_classes(driver, ["job-details-jobs-unified-top-card__primary-description-container","job-details-jobs-unified-top-card__primary-description","jobs-unified-top-card__primary-description","jobs-details__main-content"])
    about_company_org = find_by_class(driver, "jobs-company__box")
    scroll_to_view(driver, about_company_org)
    about_company_org = about_company_org.text
    about_company = about_company_org.lower()
    skip_checking = False
    for word in about_company_good_words:
        if word.lower() in about_company:
            print_lg(f'Found the word "{word}". So, skipped checking for blacklist words.')
            skip_checking = True
            break
    if not skip_checking:
        for word in about_company_bad_words: 
            if word.lower() in about_company: 
                rejected_jobs.add(job_id)
                blacklisted_companies.add(company)
                raise ValueError(f'\n"{about_company_org}"\n\nContains "{word}".')
    buffer(click_gap)
    scroll_to_view(driver, jobs_top_card)
    return rejected_jobs, blacklisted_companies, jobs_top_card, about_company_org



# Function to extract years of experience required from About Job
def extract_years_of_experience(text: str) -> int:
    # Extract all patterns like '10+ years', '5 years', '3-5 years', etc.
    matches = re.findall(re_experience, text)
    if len(matches) == 0: 
        print_lg(f'\n{text}\n\nCouldn\'t find experience requirement in About the Job!')
        return 0
    return max([int(match) for match in matches if int(match) <= 12])



def get_job_description(
) -> tuple[
    str | Literal['Unknown'],
    int | Literal['Unknown'],
    bool,
    str | None,
    str | None
    ]:
    '''
    # Job Description
    Function to extract job description from About the Job.
    ### Returns:
    - `jobDescription: str | 'Unknown'`
    - `experience_required: int | 'Unknown'`
    - `skip: bool`
    - `skipReason: str | None`
    - `skipMessage: str | None`
    '''
    try:
        ##> ------ Dheeraj Deshwal : dheeraj9811 Email:dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Feature ------
        jobDescription = "Unknown"
        ##<
        experience_required = "Unknown"
        found_masters = 0
        jobDescription = find_by_class(driver, "jobs-box__html-content").text
        jobDescriptionLow = jobDescription.lower()
        skip = False
        skipReason = None
        skipMessage = None
        for word in bad_words:
            if word.lower() in jobDescriptionLow:
                skipMessage = f'\n{jobDescription}\n\nContains bad word "{word}". Skipping this job!\n'
                skipReason = "Found a Bad Word in About Job"
                skip = True
                break
        if not skip and security_clearance == False and ('polygraph' in jobDescriptionLow or 'clearance' in jobDescriptionLow or 'secret' in jobDescriptionLow):
            skipMessage = f'\n{jobDescription}\n\nFound "Clearance" or "Polygraph". Skipping this job!\n'
            skipReason = "Asking for Security clearance"
            skip = True
        if not skip:
            if did_masters and 'master' in jobDescriptionLow:
                print_lg(f'Found the word "master" in \n{jobDescription}')
                found_masters = 2
            experience_required = extract_years_of_experience(jobDescription)
            if current_experience > -1 and experience_required > current_experience + found_masters:
                skipMessage = f'\n{jobDescription}\n\nExperience required {experience_required} > Current Experience {current_experience + found_masters}. Skipping this job!\n'
                skipReason = "Required experience is high"
                skip = True
    except Exception as e:
        if jobDescription == "Unknown":    print_lg("Unable to extract job description!")
        else:
            experience_required = "Error in extraction"
            print_lg("Unable to extract years of experience required!")
            # print_lg(e)
    finally:
        return jobDescription, experience_required, skip, skipReason, skipMessage
        


# Function to upload resume
def upload_resume(modal: WebElement, resume: str) -> tuple[bool, str]:
    try:
        modal.find_element(By.NAME, "file").send_keys(os.path.abspath(resume))
        return True, os.path.basename(resume)
    except: return False, "Previous resume"

# Function to answer common questions for Easy Apply
def select_preferred_email(select: Select, options_text: list[str], preferred_email: str, label_org: str) -> str:
    try:
        select.select_by_visible_text(preferred_email)
        return preferred_email
    except NoSuchElementException:
        for option in options_text:
            if preferred_email.lower() == option.strip().lower() or preferred_email.lower() in option.lower():
                select.select_by_visible_text(option)
                return option
        for option in options_text:
            if preferred_email.split('@')[0].lower() in option.lower() and '@' in option:
                select.select_by_visible_text(option)
                return option
        print_lg(f'Warning: "{preferred_email}" not found in email dropdown for "{label_org}". Options: {options_text}. Keeping: {select.first_selected_option.text}')
        return select.first_selected_option.text


def answer_common_questions(label: str, answer: str) -> str:
    if 'sponsorship' in label or 'visa' in label: answer = require_visa
    return answer


# Function to answer the questions for Easy Apply
def answer_questions(modal: WebElement, questions_list: set, work_location: str, job_description: str | None = None ) -> set:
    # Get all questions from the page
     
    all_questions = modal.find_elements(By.XPATH, ".//div[@data-test-form-element]")
    # all_questions = modal.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-element")
    # all_list_questions = modal.find_elements(By.XPATH, ".//div[@data-test-text-entity-list-form-component]")
    # all_single_line_questions = modal.find_elements(By.XPATH, ".//div[@data-test-single-line-text-form-component]")
    # all_questions = all_questions + all_list_questions + all_single_line_questions

    for Question in all_questions:
        # Check if it's a select Question
        select = try_xp(Question, ".//select", False)
        if select:
            label_org = "Unknown"
            try:
                label = Question.find_element(By.TAG_NAME, "label")
                label_org = label.find_element(By.TAG_NAME, "span").text
            except: pass
            answer = 'Yes'
            label = label_org.lower()
            select = Select(select)
            selected_option = select.first_selected_option.text
            optionsText = []
            options = '"List of phone country codes"'
            if label != "phone country code":
                optionsText = [option.text for option in select.options]
                options = "".join([f' "{option}",' for option in optionsText])
            prev_answer = selected_option
            if 'email' in label:
                answer = select_preferred_email(select, optionsText, email, label_org)
                questions_list.add((f'{label_org} [ {options} ]', answer, "select", prev_answer))
                continue
            if overwrite_previous_answers or selected_option == "Select an option":
                ##> ------ WINDY_WINDWARD Email:karthik.sarode23@gmail.com - Added fuzzy logic to answer location based questions ------
                if 'phone' in label: 
                    answer = prev_answer
                elif 'gender' in label or 'sex' in label: 
                    answer = gender
                elif 'disability' in label: 
                    answer = disability_status
                elif 'proficiency' in label: 
                    answer = 'Professional'
                # Add location handling
                elif any(loc_word in label for loc_word in ['location', 'city', 'state', 'country']):
                    if 'country' in label:
                        answer = country 
                    elif 'state' in label:
                        answer = state
                    elif 'city' in label:
                        answer = current_city if current_city else work_location
                    else:
                        answer = work_location
                else: 
                    answer = answer_common_questions(label,answer)
                try: 
                    select.select_by_visible_text(answer)
                except NoSuchElementException as e:
                    # Define similar phrases for common answers
                    possible_answer_phrases = []
                    if answer == 'Decline':
                        possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"]
                    elif 'yes' in answer.lower():
                        possible_answer_phrases = ["Yes", "Agree", "I do", "I have"]
                    elif 'no' in answer.lower():
                        possible_answer_phrases = ["No", "Disagree", "I don't", "I do not"]
                    else:
                        # Try partial matching for any answer
                        possible_answer_phrases = [answer]
                        # Add lowercase and uppercase variants
                        possible_answer_phrases.append(answer.lower())
                        possible_answer_phrases.append(answer.upper())
                        # Try without special characters
                        possible_answer_phrases.append(''.join(c for c in answer if c.isalnum()))
                    ##<
                    foundOption = False
                    for phrase in possible_answer_phrases:
                        for option in optionsText:
                            # Check if phrase is in option or option is in phrase (bidirectional matching)
                            if phrase.lower() in option.lower() or option.lower() in phrase.lower():
                                select.select_by_visible_text(option)
                                answer = option
                                foundOption = True
                                break
                    if not foundOption:
                        #TODO: Use AI to answer the question need to be implemented logic to extract the options for the question
                        print_lg(f'Failed to find an option with text "{answer}" for question labelled "{label_org}", answering randomly!')
                        select.select_by_index(randint(1, len(select.options)-1))
                        answer = select.first_selected_option.text
                        randomly_answered_questions.add((f'{label_org} [ {options} ]',"select"))
            questions_list.add((f'{label_org} [ {options} ]', answer, "select", prev_answer))
            continue
        
        # Check if it's a radio Question
        radio = try_xp(Question, './/fieldset[@data-test-form-builder-radio-button-form-component="true"]', False)
        if radio:
            prev_answer = None
            label = try_xp(radio, './/span[@data-test-form-builder-radio-button-form-component__title]', False)
            try: label = find_by_class(label, "visually-hidden", 2.0)
            except: pass
            label_org = label.text if label else "Unknown"
            answer = 'Yes'
            label = label_org.lower()

            label_org += ' [ '
            options = radio.find_elements(By.TAG_NAME, 'input')
            options_labels = []
            
            for option in options:
                id = option.get_attribute("id")
                option_label = try_xp(radio, f'.//label[@for="{id}"]', False)
                options_labels.append( f'"{option_label.text if option_label else "Unknown"}"<{option.get_attribute("value")}>' ) # Saving option as "label <value>"
                if option.is_selected(): prev_answer = options_labels[-1]
                label_org += f' {options_labels[-1]},'

            if overwrite_previous_answers or prev_answer is None:
                if 'citizenship' in label or 'employment eligibility' in label: answer = us_citizenship
                elif 'veteran' in label or 'protected' in label: answer = veteran_status
                elif 'disability' in label or 'handicapped' in label: 
                    answer = disability_status
                else: answer = answer_common_questions(label,answer)
                foundOption = try_xp(radio, f".//label[normalize-space()='{answer}']", False)
                if foundOption: 
                    actions.move_to_element(foundOption).click().perform()
                else:    
                    possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"] if answer == 'Decline' else [answer]
                    ele = options[0]
                    answer = options_labels[0]
                    for phrase in possible_answer_phrases:
                        for i, option_label in enumerate(options_labels):
                            if phrase in option_label:
                                foundOption = options[i]
                                ele = foundOption
                                answer = f'Decline ({option_label})' if len(possible_answer_phrases) > 1 else option_label
                                break
                        if foundOption: break
                    # if answer == 'Decline':
                    #     answer = options_labels[0]
                    #     for phrase in ["Prefer not", "not want", "not wish"]:
                    #         foundOption = try_xp(radio, f".//label[normalize-space()='{phrase}']", False)
                    #         if foundOption:
                    #             answer = f'Decline ({phrase})'
                    #             ele = foundOption
                    #             break
                    actions.move_to_element(ele).click().perform()
                    if not foundOption: randomly_answered_questions.add((f'{label_org} ]',"radio"))
            else: answer = prev_answer
            questions_list.add((label_org+" ]", answer, "radio", prev_answer))
            continue
        
        # Check if it's a text question
        text = try_xp(Question, ".//input[@type='text']", False)
        if not text:
            text = try_xp(Question, ".//input[@type='email']", False)
        if text: 
            do_actions = False
            label = try_xp(Question, ".//label[@for]", False)
            try: label = label.find_element(By.CLASS_NAME,'visually-hidden')
            except: pass
            label_org = label.text if label else "Unknown"
            answer = "" # years_of_experience
            label = label_org.lower()

            prev_answer = text.get_attribute("value")
            if 'email' in label:
                answer = email
                text.clear()
                text.send_keys(answer)
                questions_list.add((label, text.get_attribute("value"), "text", prev_answer))
                continue
            if not prev_answer or overwrite_previous_answers:
                if 'experience' in label or 'years' in label: answer = years_of_experience
                elif 'phone' in label or 'mobile' in label: answer = phone_number
                elif 'street' in label: answer = street
                elif 'city' in label or 'location' in label or 'address' in label:
                    answer = current_city if current_city else work_location
                    do_actions = True
                elif 'signature' in label: answer = full_name # 'signature' in label or 'legal name' in label or 'your name' in label or 'full name' in label: answer = full_name     # What if question is 'name of the city or university you attend, name of referral etc?'
                elif 'name' in label:
                    if 'full' in label: answer = full_name
                    elif 'first' in label and 'last' not in label: answer = first_name
                    elif 'middle' in label and 'last' not in label: answer = middle_name
                    elif 'last' in label and 'first' not in label: answer = last_name
                    elif 'employer' in label: answer = recent_employer
                    else: answer = full_name
                elif 'notice' in label:
                    if 'month' in label:
                        answer = notice_period_months
                    elif 'week' in label:
                        answer = notice_period_weeks
                    else: answer = notice_period
                elif 'salary' in label or 'compensation' in label or 'ctc' in label or 'pay' in label: 
                    if 'current' in label or 'present' in label:
                        if 'month' in label:
                            answer = current_ctc_monthly
                        elif 'lakh' in label:
                            answer = current_ctc_lakhs
                        else:
                            answer = current_ctc
                    else:
                        if 'month' in label:
                            answer = desired_salary_monthly
                        elif 'lakh' in label:
                            answer = desired_salary_lakhs
                        else:
                            answer = desired_salary
                elif 'linkedin' in label: answer = linkedIn
                elif 'website' in label or 'blog' in label or 'portfolio' in label or 'link' in label: answer = website
                elif 'scale of 1-10' in label: answer = confidence_level
                elif 'headline' in label: answer = linkedin_headline
                elif ('hear' in label or 'come across' in label) and 'this' in label and ('job' in label or 'position' in label): answer = "https://github.com/GodsScion/Auto_job_applier_linkedIn"
                elif 'state' in label or 'province' in label: answer = state
                elif 'zip' in label or 'postal' in label or 'code' in label: answer = zipcode
                elif 'country' in label: answer = country
                else: answer = answer_common_questions(label,answer)
                ##> ------ Yang Li : MARKYangL - Feature ------
                if answer == "":
                    if use_AI and aiClient:
                        try:
                            if ai_provider.lower() == "openai":
                                answer = ai_answer_question(aiClient, label_org, question_type="text", job_description=job_description, user_information_all=user_information_all)
                            elif ai_provider.lower() == "deepseek":
                                answer = deepseek_answer_question(aiClient, label_org, options=None, question_type="text", job_description=job_description, about_company=None, user_information_all=user_information_all)
                            elif ai_provider.lower() == "gemini":
                                answer = gemini_answer_question(aiClient, label_org, options=None, question_type="text", job_description=job_description, about_company=None, user_information_all=user_information_all)
                            else:
                                randomly_answered_questions.add((label_org, "text"))
                                answer = years_of_experience
                            if answer and isinstance(answer, str) and len(answer) > 0:
                                print_lg(f'AI Answered received for question "{label_org}" \nhere is answer: "{answer}"')
                            else:
                                randomly_answered_questions.add((label_org, "text"))
                                answer = years_of_experience
                        except Exception as e:
                            print_lg("Failed to get AI answer!", e)
                            randomly_answered_questions.add((label_org, "text"))
                            answer = years_of_experience
                    else:
                        randomly_answered_questions.add((label_org, "text"))
                        answer = years_of_experience
                ##<
                text.clear()
                text.send_keys(answer)
                if do_actions:
                    sleep(2)
                    actions.send_keys(Keys.ARROW_DOWN)
                    actions.send_keys(Keys.ENTER).perform()
            questions_list.add((label, text.get_attribute("value"), "text", prev_answer))
            continue

        # Check if it's a textarea question
        text_area = try_xp(Question, ".//textarea", False)
        if text_area:
            label = try_xp(Question, ".//label[@for]", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = ""
            prev_answer = text_area.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                if 'summary' in label: answer = linkedin_summary
                elif 'cover' in label: answer = cover_letter
                if answer == "":
                ##> ------ Yang Li : MARKYangL - Feature ------
                    if use_AI and aiClient:
                        try:
                            if ai_provider.lower() == "openai":
                                answer = ai_answer_question(aiClient, label_org, question_type="textarea", job_description=job_description, user_information_all=user_information_all)
                            elif ai_provider.lower() == "deepseek":
                                answer = deepseek_answer_question(aiClient, label_org, options=None, question_type="textarea", job_description=job_description, about_company=None, user_information_all=user_information_all)
                            elif ai_provider.lower() == "gemini":
                                answer = gemini_answer_question(aiClient, label_org, options=None, question_type="textarea", job_description=job_description, about_company=None, user_information_all=user_information_all)
                            else:
                                randomly_answered_questions.add((label_org, "textarea"))
                                answer = ""
                            if answer and isinstance(answer, str) and len(answer) > 0:
                                print_lg(f'AI Answered received for question "{label_org}" \nhere is answer: "{answer}"')
                            else:
                                randomly_answered_questions.add((label_org, "textarea"))
                                answer = ""
                        except Exception as e:
                            print_lg("Failed to get AI answer!", e)
                            randomly_answered_questions.add((label_org, "textarea"))
                            answer = ""
                    else:
                        randomly_answered_questions.add((label_org, "textarea"))
            text_area.clear()
            text_area.send_keys(answer)
            if do_actions:
                    sleep(2)
                    actions.send_keys(Keys.ARROW_DOWN)
                    actions.send_keys(Keys.ENTER).perform()
            questions_list.add((label, text_area.get_attribute("value"), "textarea", prev_answer))
            ##<
            continue

        # Check if it's a checkbox question
        checkbox = try_xp(Question, ".//input[@type='checkbox']", False)
        if checkbox:
            label = try_xp(Question, ".//span[@class='visually-hidden']", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = try_xp(Question, ".//label[@for]", False)  # Sometimes multiple checkboxes are given for 1 question, Not accounted for that yet
            answer = answer.text if answer else "Unknown"
            prev_answer = checkbox.is_selected()
            checked = prev_answer
            if not prev_answer:
                try:
                    actions.move_to_element(checkbox).click().perform()
                    checked = True
                except Exception as e: 
                    print_lg("Checkbox click failed!", e)
                    pass
            questions_list.add((f'{label} ([X] {answer})', checked, "checkbox", prev_answer))
            continue


    # Select todays date
    try_xp(driver, "//button[contains(@aria-label, 'This is today')]")

    # Collect important skills
    # if 'do you have' in label and 'experience' in label and ' in ' in label -> Get word (skill) after ' in ' from label
    # if 'how many years of experience do you have in ' in label -> Get word (skill) after ' in '

    return questions_list




def external_apply(pagination_element: WebElement, job_id: str, job_link: str, resume: str, date_listed, application_link: str, screenshot_name: str) -> tuple[bool, str, int]:
    '''
    Function to open new tab and save external job application links
    '''
    global tabs_count, dailyEasyApplyLimitReached
    if easy_apply_only:
        try:
            if "exceeded the daily application limit" in driver.find_element(By.CLASS_NAME, "artdeco-inline-feedback__message").text: dailyEasyApplyLimitReached = True
        except: pass
        print_lg("Easy apply failed I guess!")
        if pagination_element != None: return True, application_link, tabs_count
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3')]"))).click() # './/button[contains(span, "Apply") and not(span[contains(@class, "disabled")])]'
        wait_span_click(driver, "Continue", 1, True, False)
        windows = driver.window_handles
        tabs_count = len(windows)
        driver.switch_to.window(windows[-1])
        application_link = driver.current_url
        print_lg('Got the external application link "{}"'.format(application_link))
        if close_tabs and driver.current_window_handle != linkedIn_tab: driver.close()
        driver.switch_to.window(linkedIn_tab)
        return False, application_link, tabs_count
    except Exception as e:
        # print_lg(e)
        print_lg("Failed to apply!")
        failed_job(job_id, job_link, resume, date_listed, "Probably didn't find Apply button or unable to switch tabs.", e, application_link, screenshot_name)
        global failed_count
        failed_count += 1
        return True, application_link, tabs_count



def follow_company(modal: WebDriver = driver) -> None:
    '''
    Function to follow or un-follow easy applied companies based om `follow_companies`
    '''
    try:
        follow_checkbox_input = try_xp(modal, ".//input[@id='follow-company-checkbox' and @type='checkbox']", False)
        if follow_checkbox_input and follow_checkbox_input.is_selected() != follow_companies:
            try_xp(modal, ".//label[@for='follow-company-checkbox']")
    except Exception as e:
        print_lg("Failed to update follow companies checkbox!", e)
    


#< Failed attempts logging
def failed_job(job_id: str, job_link: str, resume: str, date_listed, error: str, exception: Exception, application_link: str, screenshot_name: str) -> None:
    '''
    Function to update failed jobs list in excel
    '''
    try:
        with open(failed_file_name, 'a', newline='', encoding='utf-8') as file:
            fieldnames = ['Job ID', 'Job Link', 'Resume Tried', 'Date listed', 'Date Tried', 'Assumed Reason', 'Stack Trace', 'External Job link', 'Screenshot Name']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':truncate_for_csv(job_id), 'Job Link':truncate_for_csv(job_link), 'Resume Tried':truncate_for_csv(resume), 'Date listed':truncate_for_csv(date_listed), 'Date Tried':datetime.now(), 'Assumed Reason':truncate_for_csv(error), 'Stack Trace':truncate_for_csv(exception), 'External Job link':truncate_for_csv(application_link), 'Screenshot Name':truncate_for_csv(screenshot_name)})
            file.close()
    except Exception as e:
        print_lg("Failed to update failed jobs list!", e)


def screenshot(driver: WebDriver, job_id: str, failedAt: str) -> str:
    '''
    Function to to take screenshot for debugging
    - Returns screenshot name as String
    '''
    screenshot_name = "{} - {} - {}.png".format( job_id, failedAt, str(datetime.now()) )
    path = logs_folder_path+"/screenshots/"+screenshot_name.replace(":",".")
    # special_chars = {'*', '"', '\\', '<', '>', ':', '|', '?'}
    # for char in special_chars:  path = path.replace(char, '-')
    driver.save_screenshot(path.replace("//","/"))
    return screenshot_name
#>



def submitted_jobs(job_id: str, title: str, company: str, work_location: str, work_style: str, description: str, experience_required: int | Literal['Unknown', 'Error in extraction'], 
                   skills: list[str] | Literal['In Development'], hr_name: str | Literal['Unknown'], hr_link: str | Literal['Unknown'], resume: str, 
                   reposted: bool, date_listed: datetime | Literal['Unknown'], date_applied:  datetime | Literal['Pending'], job_link: str, application_link: str, 
                   questions_list: set | None, connect_request: Literal['In Development']) -> None:
    '''
    Function to create or update the Applied jobs CSV file, once the application is submitted successfully
    '''
    try:
        with open(file_name, mode='a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 'About Job', 'Experience required', 'Skills required', 'HR Name', 'HR Link', 'Resume', 'Re-posted', 'Date Posted', 'Date Applied', 'Job Link', 'External Job link', 'Questions Found', 'Connect Request']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if csv_file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':truncate_for_csv(job_id), 'Title':truncate_for_csv(title), 'Company':truncate_for_csv(company), 'Work Location':truncate_for_csv(work_location), 'Work Style':truncate_for_csv(work_style), 
                            'About Job':truncate_for_csv(description), 'Experience required': truncate_for_csv(experience_required), 'Skills required':truncate_for_csv(skills), 
                                'HR Name':truncate_for_csv(hr_name), 'HR Link':truncate_for_csv(hr_link), 'Resume':truncate_for_csv(resume), 'Re-posted':truncate_for_csv(reposted), 
                                'Date Posted':truncate_for_csv(date_listed), 'Date Applied':truncate_for_csv(date_applied), 'Job Link':truncate_for_csv(job_link), 
                                'External Job link':truncate_for_csv(application_link), 'Questions Found':truncate_for_csv(questions_list), 'Connect Request':truncate_for_csv(connect_request)})
        csv_file.close()
    except Exception as e:
        print_lg("Failed to update submitted jobs list!", e)



# Function to discard the job application
def discard_job() -> None:
    actions.send_keys(Keys.ESCAPE).perform()
    wait_span_click(driver, 'Discard', 2)






# Function to apply to jobs
def apply_to_jobs(search_terms: list[str] | None = None, saved_jobs_mode: bool = False) -> None:
    applied_jobs = get_applied_job_ids()
    saved_jobs_ids = get_saved_job_ids() if save_jobs_only else set()
    rejected_jobs = set()
    blacklisted_companies = set()
    global current_city, failed_count, skip_count, easy_applied_count, external_jobs_count, bookmarked_count, tabs_count, pause_before_submit, pause_at_failed_question, useNewResume
    current_city = current_city.strip()
    use_search_filters = not (saved_jobs_mode and relax_filters_for_saved_jobs)
    job_limit = saved_jobs_limit if saved_jobs_mode and saved_jobs_limit > 0 else (switch_number if not saved_jobs_mode else 99999)

    search_runs = [None] if saved_jobs_mode else (list(search_terms) if search_terms else [])
    if randomize_search_order and not saved_jobs_mode:  shuffle(search_runs)

    for searchTerm in search_runs:
        if saved_jobs_mode and save_jobs_only:
            continue
        active_listing_xpath = None
        if saved_jobs_mode:
            print_lg("\n________________________________________________________________________________________________________________________\n")
            print_lg('\n>>>> STEP 1: Applying to your Saved jobs on LinkedIn <<<<\n\n')
            active_listing_xpath = open_saved_jobs_page()
            if not active_listing_xpath:
                print_lg("No saved jobs found in your LinkedIn Saved list. Continuing with keyword search...")
                continue
        else:
            driver.get(f"https://www.linkedin.com/jobs/search/?keywords={searchTerm}")
            print_lg("\n________________________________________________________________________________________________________________________\n")
            if save_jobs_only:
                print_lg(f'\n>>>> Bookmarking jobs for "{searchTerm}" (no apply) <<<<\n\n')
            else:
                print_lg(f'\n>>>> STEP 2: Searching and applying — "{searchTerm}" <<<<\n\n')
            apply_filters()
            buffer(3)
            active_listing_xpath = wait_for_job_listings(12)
            if not active_listing_xpath:
                print_lg(f'No job listings found for "{searchTerm}", skipping this search term.')
                continue

        current_count = 0
        try:
            while current_count < job_limit:
                active_listing_xpath = wait_for_job_listings(8) or active_listing_xpath
                if not active_listing_xpath:
                    break

                pagination_element, current_page = get_page_info()

                # Find all job listings in current page
                buffer(3)
                job_listings = get_job_listings(active_listing_xpath)
                if not job_listings:
                    if saved_jobs_mode:
                        print_lg("No more saved jobs to process on this page.")
                    break  

            
                for job in job_listings:
                    if keep_screen_awake: pyautogui.press('shiftright')
                    if current_count >= job_limit: break
                    print_lg("\n-@-\n")

                    job_id,title,company,work_location,work_style,skip = get_job_main_details(job, blacklisted_companies, rejected_jobs, use_search_filters)
                    
                    if skip: continue
                    if save_jobs_only and job_id in saved_jobs_ids:
                        print_lg(f'Already bookmarked "{title} | {company}" job. Job ID: {job_id}!')
                        continue
                    # Redundant fail safe check for applied jobs!
                    if not save_jobs_only:
                        try:
                            if job_id in applied_jobs or find_by_class(driver, "jobs-s-apply__application-link", 2):
                                print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
                                continue
                        except Exception as e:
                            print_lg(f'Trying to Apply to "{title} | {company}" job. Job ID: {job_id}')
                    else:
                        print_lg(f'Trying to bookmark "{title} | {company}" job. Job ID: {job_id}')

                    job_link = "https://www.linkedin.com/jobs/view/"+job_id
                    application_link = "Easy Applied"
                    date_applied = "Pending"
                    hr_link = "Unknown"
                    hr_name = "Unknown"
                    connect_request = "In Development" # Still in development
                    date_listed = "Unknown"
                    skills = "Needs an AI" # Still in development
                    resume = "Pending"
                    reposted = False
                    questions_list = None
                    screenshot_name = "Not Available"

                    jobs_top_card = None
                    about_company_text = ""
                    try:
                        rejected_jobs, blacklisted_companies, jobs_top_card, about_company_text = check_blacklist(rejected_jobs,job_id,company,blacklisted_companies)
                    except ValueError as e:
                        print_lg(e, 'Skipping this job!\n')
                        failed_job(job_id, job_link, resume, date_listed, "Found Blacklisted words in About Company", e, "Skipped", screenshot_name)
                        skip_count += 1
                        continue
                    except Exception as e:
                        print_lg("Failed to scroll to About Company!", e)
                        jobs_top_card = try_find_by_classes(driver, ["job-details-jobs-unified-top-card__primary-description-container","job-details-jobs-unified-top-card__primary-description","jobs-unified-top-card__primary-description","jobs-details__main-content"])

                    if jobs_top_card:
                        detail_location, detail_style = extract_work_location_from_top_card(jobs_top_card)
                        if detail_location:
                            work_location = detail_location
                        if detail_style:
                            work_style = detail_style
                    if use_search_filters:
                        skip_for_location, location_reason = should_skip_for_location(work_location, work_style)
                        if skip_for_location:
                            print_lg(f'Skipping "{title} | {company}" job ({location_reason}). Job ID: {job_id}!')
                            failed_job(job_id, job_link, resume, date_listed, "Location filter", location_reason, "Skipped", screenshot_name)
                            rejected_jobs.add(job_id)
                            skip_count += 1
                            continue

                        skip_for_company_size, company_size_reason, company_size = should_skip_for_company_size(about_company_text, jobs_top_card)
                        if skip_for_company_size:
                            print_lg(f'Skipping "{title} | {company}" job ({company_size_reason}). Job ID: {job_id}!')
                            failed_job(job_id, job_link, resume, date_listed, "Company size filter", company_size_reason, "Skipped", screenshot_name)
                            rejected_jobs.add(job_id)
                            skip_count += 1
                            continue
                        if company_size:
                            print_lg(f'Company size detected: {company_size:,} employees')


                    # Hiring Manager info
                    try:
                        hr_info_card = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, "hirer-card__hirer-information")))
                        hr_link = hr_info_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                        hr_name = hr_info_card.find_element(By.TAG_NAME, "span").text
                        # if connect_hr:
                        #     driver.switch_to.new_window('tab')
                        #     driver.get(hr_link)
                        #     wait_span_click("More")
                        #     wait_span_click("Connect")
                        #     wait_span_click("Add a note")
                        #     message_box = driver.find_element(By.XPATH, "//textarea")
                        #     message_box.send_keys(connect_request_message)
                        #     if close_tabs: driver.close()
                        #     driver.switch_to.window(linkedIn_tab) 
                        # def message_hr(hr_info_card):
                        #     if not hr_info_card: return False
                        #     hr_info_card.find_element(By.XPATH, ".//span[normalize-space()='Message']").click()
                        #     message_box = driver.find_element(By.XPATH, "//div[@aria-label='Write a message…']")
                        #     message_box.send_keys()
                        #     try_xp(driver, "//button[normalize-space()='Send']")        
                    except Exception as e:
                        print_lg(f'HR info was not given for "{title}" with Job ID: {job_id}!')
                        # print_lg(e)


                    # Calculation of date posted
                    try:
                        # try: time_posted_text = find_by_class(driver, "jobs-unified-top-card__posted-date", 2).text
                        # except: 
                        time_posted_text = jobs_top_card.find_element(By.XPATH, './/span[contains(normalize-space(), " ago")]').text
                        print("Time Posted: " + time_posted_text)
                        if time_posted_text.__contains__("Reposted"):
                            reposted = True
                            time_posted_text = time_posted_text.replace("Reposted", "")
                        date_listed = calculate_date_posted(time_posted_text.strip())
                        if use_search_filters and max_days_since_posted > 0 and date_listed and (datetime.now() - date_listed).days > max_days_since_posted:
                            print_lg(f'Skipping "{title} | {company}" job (Posted {time_posted_text.strip()}, older than {max_days_since_posted} days). Job ID: {job_id}!')
                            failed_job(job_id, job_link, resume, date_listed, "Job too old", f"Posted more than {max_days_since_posted} days ago", "Skipped", screenshot_name)
                            rejected_jobs.add(job_id)
                            skip_count += 1
                            continue
                    except Exception as e:
                        print_lg("Failed to calculate the date posted!",e)


                    description, experience_required, skip, reason, message = get_job_description()
                    if skip:
                        print_lg(message)
                        failed_job(job_id, job_link, resume, date_listed, reason, message, "Skipped", screenshot_name)
                        rejected_jobs.add(job_id)
                        skip_count += 1
                        continue

                    
                    if use_AI and description != "Unknown":
                        ##> ------ Yang Li : MARKYangL - Feature ------
                        try:
                            if ai_provider.lower() == "openai":
                                skills = ai_extract_skills(aiClient, description)
                            elif ai_provider.lower() == "deepseek":
                                skills = deepseek_extract_skills(aiClient, description)
                            elif ai_provider.lower() == "gemini":
                                skills = gemini_extract_skills(aiClient, description)
                            else:
                                skills = "In Development"
                            print_lg(f"Extracted skills using {ai_provider} AI")
                        except Exception as e:
                            print_lg("Failed to extract skills:", e)
                            skills = "Error extracting skills"
                        ##<

                    if save_jobs_only:
                        refreshed_job = find_job_card_by_id(job_id)
                        if refreshed_job:
                            job = refreshed_job
                        save_ok, save_status = save_job_on_linkedin(job)
                        if save_ok:
                            record_saved_job(job_id, title, company, work_location, work_style, job_link, save_status)
                            bookmarked_count += 1
                            saved_jobs_ids.add(job_id)
                            print_lg(f'Successfully bookmarked "{title} | {company}" job. Job ID: {job_id}!')
                            current_count += 1
                        else:
                            print_lg(f'Failed to bookmark "{title} | {company}" job. Job ID: {job_id}! {save_status}')
                            failed_job(job_id, job_link, resume, date_listed, "Failed to save job", save_status, "Failed", screenshot_name)
                            failed_count += 1
                        continue

                    uploaded = False
                    # Case 1: Easy Apply Button
                    # First try the classic button with "Easy" in aria-label
                    is_easy_apply = try_xp(driver, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3') and contains(@aria-label, 'Easy')]")
                    # Fallback 1: check if apply link contains Easy Apply URL pattern
                    if not is_easy_apply:
                        try:
                            apply_link_el = driver.find_element(By.XPATH, ".//a[contains(@href, 'openSDUIApplyFlow=true')]")
                            if apply_link_el:
                                apply_link_el.click()
                                is_easy_apply = True
                                print_lg("Detected Easy Apply via URL pattern (openSDUIApplyFlow)")
                        except:
                            pass
                    # Fallback 2: click any Apply button and check if Easy Apply modal appears
                    if not is_easy_apply:
                        try:
                            apply_btn = driver.find_element(By.XPATH, ".//button[contains(@class,'jobs-apply-button')]")
                            if apply_btn:
                                tabs_before = len(driver.window_handles)
                                apply_btn.click()
                                buffer(click_gap)
                                tabs_after = len(driver.window_handles)
                                if tabs_after > tabs_before:
                                    # New tab opened — external apply, close it and go back
                                    driver.switch_to.window(driver.window_handles[-1])
                                    if close_tabs and driver.current_window_handle != linkedIn_tab: driver.close()
                                    driver.switch_to.window(linkedIn_tab)
                                    print_lg("External apply detected via new tab, skipping")
                                else:
                                    try:
                                        find_by_class(driver, "jobs-easy-apply-modal")
                                        is_easy_apply = True
                                        print_lg("Detected Easy Apply via modal appearance after click")
                                    except:
                                        # Modal didn't appear — dismiss
                                        try: actions.send_keys(Keys.ESCAPE).perform()
                                        except: pass
                        except:
                            pass
                    if is_easy_apply:
                        try: 
                            try:
                                errored = ""
                                modal = find_by_class(driver, "jobs-easy-apply-modal")
                                wait_span_click(modal, "Next", 1)
                                # if description != "Unknown":
                                #     resume = create_custom_resume(description)
                                resume = "Previous resume"
                                next_button = True
                                questions_list = set()
                                next_counter = 0
                                while next_button:
                                    next_counter += 1
                                    if next_counter >= 15: 
                                        if pause_at_failed_question:
                                            screenshot(driver, job_id, "Needed manual intervention for failed question")
                                            pyautogui.alert("Couldn't answer one or more questions.\nPlease click \"Continue\" once done.\nDO NOT CLICK Back, Next or Review button in LinkedIn.\n\n\n\n\nYou can turn off \"Pause at failed question\" setting in config.py", "Help Needed", "Continue")
                                            next_counter = 1
                                            continue
                                        if questions_list: print_lg("Stuck for one or some of the following questions...", questions_list)
                                        screenshot_name = screenshot(driver, job_id, "Failed at questions")
                                        errored = "stuck"
                                        raise Exception("Seems like stuck in a continuous loop of next, probably because of new questions.")
                                    questions_list = answer_questions(modal, questions_list, work_location, job_description=description)
                                    if useNewResume and not uploaded: uploaded, resume = upload_resume(modal, default_resume_path)
                                    try: next_button = modal.find_element(By.XPATH, './/span[normalize-space(.)="Review"]') 
                                    except NoSuchElementException:  next_button = modal.find_element(By.XPATH, './/button[contains(span, "Next")]')
                                    try: next_button.click()
                                    except ElementClickInterceptedException: break    # Happens when it tries to click Next button in About Company photos section
                                    buffer(click_gap)

                            except NoSuchElementException: errored = "nose"
                            finally:
                                if questions_list and errored != "stuck": 
                                    print_lg("Answered the following questions...", questions_list)
                                    print("\n\n" + "\n".join(str(question) for question in questions_list) + "\n\n")
                                wait_span_click(driver, "Review", 1, scrollTop=True)
                                cur_pause_before_submit = pause_before_submit
                                if errored != "stuck" and cur_pause_before_submit:
                                    decision = pyautogui.confirm('1. Please verify your information.\n2. If you edited something, please return to this final screen.\n3. DO NOT CLICK "Submit Application".\n\n\n\n\nYou can turn off "Pause before submit" setting in config.py\nTo TEMPORARILY disable pausing, click "Disable Pause"', "Confirm your information",["Disable Pause", "Discard Application", "Submit Application"])
                                    if decision == "Discard Application": raise Exception("Job application discarded by user!")
                                    pause_before_submit = False if "Disable Pause" == decision else True
                                    # try_xp(modal, ".//span[normalize-space(.)='Review']")
                                follow_company(modal)
                                if wait_span_click(driver, "Submit application", 2, scrollTop=True): 
                                    date_applied = datetime.now()
                                    if not wait_span_click(driver, "Done", 2): actions.send_keys(Keys.ESCAPE).perform()
                                elif errored != "stuck" and cur_pause_before_submit and "Yes" in pyautogui.confirm("You submitted the application, didn't you 😒?", "Failed to find Submit Application!", ["Yes", "No"]):
                                    date_applied = datetime.now()
                                    wait_span_click(driver, "Done", 2)
                                else:
                                    print_lg("Since, Submit Application failed, discarding the job application...")
                                    # if screenshot_name == "Not Available":  screenshot_name = screenshot(driver, job_id, "Failed to click Submit application")
                                    # else:   screenshot_name = [screenshot_name, screenshot(driver, job_id, "Failed to click Submit application")]
                                    if errored == "nose": raise Exception("Failed to click Submit application 😑")


                        except Exception as e:
                            print_lg("Failed to Easy apply!")
                            # print_lg(e)
                            critical_error_log("Somewhere in Easy Apply process",e)
                            failed_job(job_id, job_link, resume, date_listed, "Problem in Easy Applying", e, application_link, screenshot_name)
                            failed_count += 1
                            discard_job()
                            continue
                    else:
                        # Case 2: Apply externally
                        skip, application_link, tabs_count = external_apply(pagination_element, job_id, job_link, resume, date_listed, application_link, screenshot_name)
                        if dailyEasyApplyLimitReached:
                            print_lg("\n###############  Daily application limit for Easy Apply is reached!  ###############\n")
                            return
                        if skip: continue

                    submitted_jobs(job_id, title, company, work_location, work_style, description, experience_required, skills, hr_name, hr_link, resume, reposted, date_listed, date_applied, job_link, application_link, questions_list, connect_request)

                    print_lg(f'Successfully saved "{title} | {company}" job. Job ID: {job_id} info')
                    current_count += 1
                    if application_link == "Easy Applied": easy_applied_count += 1
                    else:   external_jobs_count += 1
                    applied_jobs.add(job_id)



                # Switching to next page
                if pagination_element == None:
                    print_lg("Couldn't find pagination element, probably at the end page of results!")
                    break
                try:
                    pagination_element.find_element(By.XPATH, f"//button[@aria-label='Page {current_page+1}']").click()
                    print_lg(f"\n>-> Now on Page {current_page+1} \n")
                except NoSuchElementException:
                    print_lg(f"\n>-> Didn't find Page {current_page+1}. Probably at the end page of results!\n")
                    break

        except (NoSuchWindowException, WebDriverException) as e:
            print_lg("Browser window closed or session is invalid. Ending application process.", e)
            raise e # Re-raise to be caught by main
        except Exception as e:
            print_lg("Failed to find Job listings!")
            critical_error_log("In Applier", e)
            try:
                print_lg(driver.page_source, pretty=True)
            except Exception as page_source_error:
                print_lg(f"Failed to get page source, browser might have crashed. {page_source_error}")
            # print_lg(e)

        
def run(total_runs: int) -> int:
    if dailyEasyApplyLimitReached and not save_jobs_only:
        return total_runs
    print_lg("\n########################################################################################################################\n")
    print_lg(f"Date and Time: {datetime.now()}")
    print_lg(f"Cycle number: {total_runs}")
    if save_jobs_only:
        print_lg("Mode: Save only (bookmark matching jobs without applying)")
    else:
        print_lg("Daily workflow: (1) Apply Saved jobs  ->  (2) Search new jobs with your filters")
    print_lg(f"Currently looking for jobs posted within '{date_posted}' and sorting them by '{sort_by}'")
    if apply_saved_jobs_first and not save_jobs_only and not dailyEasyApplyLimitReached:
        apply_to_jobs(saved_jobs_mode=True)
        if dailyEasyApplyLimitReached:
            print_lg("Daily Easy Apply limit reached after Saved jobs. Skipping new job search for this cycle.")
    if save_jobs_only or (search_new_jobs_after_saved and not dailyEasyApplyLimitReached):
        apply_to_jobs(search_terms)
    print_lg("########################################################################################################################\n")
    if not dailyEasyApplyLimitReached or save_jobs_only:
        print_lg("Sleeping for 10 min...")
        sleep(300)
        print_lg("Few more min... Gonna start with in next 5 min...")
        sleep(300)
    buffer(3)
    return total_runs + 1



chatGPT_tab = False
linkedIn_tab = False

def main() -> None:
    print_lg("Starting Auto Job Applier...")
    if save_jobs_only:
        print_lg("Save-only mode is ON — jobs that pass your filters will be bookmarked on LinkedIn, not applied to.")
    elif apply_saved_jobs_first:
        print_lg("Daily mode: first apply to your LinkedIn Saved jobs, then search and apply to new jobs matching your filters.")
    total_runs = 1
    try:
        global linkedIn_tab, tabs_count, useNewResume, aiClient
        alert_title = "Error Occurred. Closing Browser!"
        validate_config()
        
        if not os.path.exists(default_resume_path):
            print_lg('Your default resume "{}" is missing! Continuing with your previously uploaded resume from LinkedIn.'.format(default_resume_path))
            useNewResume = False
        
        # Login to LinkedIn
        tabs_count = len(driver.window_handles)
        driver.get("https://www.linkedin.com/login")
        if not is_logged_in_LN(): login_LN()
        
        linkedIn_tab = driver.current_window_handle

        # # Login to ChatGPT in a new tab for resume customization
        # if use_resume_generator:
        #     try:
        #         driver.switch_to.new_window('tab')
        #         driver.get("https://chat.openai.com/")
        #         if not is_logged_in_GPT(): login_GPT()
        #         open_resume_chat()
        #         global chatGPT_tab
        #         chatGPT_tab = driver.current_window_handle
        #     except Exception as e:
        #         print_lg("Opening OpenAI chatGPT tab failed!")
        if use_AI:
            if ai_provider == "openai":
                aiClient = ai_create_openai_client()
            ##> ------ Yang Li : MARKYangL - Feature ------
            # Create DeepSeek client
            elif ai_provider == "deepseek":
                aiClient = deepseek_create_client()
            elif ai_provider == "gemini":
                aiClient = gemini_create_client()
            ##<

            try:
                about_company_for_ai = " ".join([word for word in (first_name+" "+last_name).split() if len(word) > 3])
                print_lg(f"Extracted about company info for AI: '{about_company_for_ai}'")
            except Exception as e:
                print_lg("Failed to extract about company info!", e)
        
        # Start applying to jobs
        driver.switch_to.window(linkedIn_tab)
        total_runs = run(total_runs)
        while(run_non_stop):
            if cycle_date_posted:
                date_options = ["Any time", "Past month", "Past week", "Past 24 hours"]
                global date_posted
                date_posted = date_options[date_options.index(date_posted)+1 if date_options.index(date_posted)+1 > len(date_options) else -1] if stop_date_cycle_at_24hr else date_options[0 if date_options.index(date_posted)+1 >= len(date_options) else date_options.index(date_posted)+1]
            if alternate_sortby:
                global sort_by
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
                total_runs = run(total_runs)
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
            total_runs = run(total_runs)
            if dailyEasyApplyLimitReached and not save_jobs_only:
                break
        

    except (NoSuchWindowException, WebDriverException) as e:
        print_lg("Browser window closed or session is invalid. Exiting.", e)
    except Exception as e:
        critical_error_log("In Applier Main", e)
        print_lg(e, alert_title)
    finally:
        summary = "Total runs: {}\nJobs bookmarked: {}\nJobs Easy Applied: {}\nExternal job links collected: {}\nTotal applied or collected: {}\nFailed jobs: {}\nIrrelevant jobs skipped: {}\n".format(total_runs,bookmarked_count,easy_applied_count,external_jobs_count,easy_applied_count + external_jobs_count + bookmarked_count,failed_count,skip_count)
        print_lg(summary)
        print_lg("\n\nTotal runs:                     {}".format(total_runs))
        if save_jobs_only:
            print_lg("Jobs bookmarked:                {}".format(bookmarked_count))
        print_lg("Jobs Easy Applied:              {}".format(easy_applied_count))
        print_lg("External job links collected:   {}".format(external_jobs_count))
        print_lg("                              ----------")
        print_lg("Total applied or collected:     {}".format(easy_applied_count + external_jobs_count + bookmarked_count))
        print_lg("\nFailed jobs:                    {}".format(failed_count))
        print_lg("Irrelevant jobs skipped:        {}\n".format(skip_count))
        if randomly_answered_questions: print_lg("\n\nQuestions randomly answered:\n  {}  \n\n".format(";\n".join(str(question) for question in randomly_answered_questions)))
        quotes = choice([
            "Never quit. You're one step closer than before. - Sai Vignesh Golla", 
            "All the best with your future interviews, you've got this. - Sai Vignesh Golla", 
            "Keep up with the progress. You got this. - Sai Vignesh Golla", 
            "If you're tired, learn to take rest but never give up. - Sai Vignesh Golla",
            "Success is not final, failure is not fatal, It is the courage to continue that counts. - Winston Churchill (Not a sponsor)",
            "Believe in yourself and all that you are. Know that there is something inside you that is greater than any obstacle. - Christian D. Larson (Not a sponsor)",
            "Every job is a self-portrait of the person who does it. Autograph your work with excellence. - Jessica Guidobono (Not a sponsor)",
            "The only way to do great work is to love what you do. If you haven't found it yet, keep looking. Don't settle. - Steve Jobs (Not a sponsor)",
            "Opportunities don't happen, you create them. - Chris Grosser (Not a sponsor)",
            "The road to success and the road to failure are almost exactly the same. The difference is perseverance. - Colin R. Davis (Not a sponsor)",
            "Obstacles are those frightful things you see when you take your eyes off your goal. - Henry Ford (Not a sponsor)",
            "The only limit to our realization of tomorrow will be our doubts of today. - Franklin D. Roosevelt (Not a sponsor)",
            ])
        sponsors = "Be the first to have your name here!"
        timeSaved = (easy_applied_count * 80) + (external_jobs_count * 20) + (skip_count * 10)
        timeSavedMsg = ""
        if timeSaved > 0:
            timeSaved += 60
            timeSavedMsg = f"In this run, you saved approx {round(timeSaved/60)} mins ({timeSaved} secs), please consider supporting the project."
        msg = f"{quotes}\n\n\n{timeSavedMsg}\nYou can also get your quote and name shown here, or prioritize your bug reports by supporting the project at:\n\nhttps://github.com/sponsors/GodsScion\n\n\nSummary:\n{summary}\n\n\nBest regards,\nSai Vignesh Golla\nhttps://www.linkedin.com/in/saivigneshgolla/\n\nTop Sponsors:\n{sponsors}"
        print_lg(msg,"Closing the browser...")
        if tabs_count >= 10:
            msg = "NOTE: IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM!\n\nOr it's highly likely that application will just open browser and not do anything next time!" 
            print_lg(msg)
            print_lg("\n"+msg)
        ##> ------ Yang Li : MARKYangL - Feature ------
        if use_AI and aiClient:
            try:
                if ai_provider.lower() == "openai":
                    ai_close_openai_client(aiClient)
                elif ai_provider.lower() == "deepseek":
                    ai_close_openai_client(aiClient)
                elif ai_provider.lower() == "gemini":
                    pass # Gemini client does not need to be closed
                print_lg(f"Closed {ai_provider} AI client.")
            except Exception as e:
                print_lg("Failed to close AI client:", e)
        ##<
        try:
            if driver:
                driver.quit()
        except WebDriverException as e:
            print_lg("Browser already closed.", e)
        except Exception as e: 
            critical_error_log("When quitting...", e)


if __name__ == "__main__":
    main()
