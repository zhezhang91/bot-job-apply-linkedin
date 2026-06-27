'''
Fill job application forms on external company websites (Workday, Greenhouse, etc.).
Does not auto-submit by default — leaves the tab open for manual review and submit.
'''

import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    WebDriverException,
)

from config.personals import *
from config.questions import *
from config.search import external_apply_max_steps, fill_external_application_forms, external_auto_submit
from config.settings import click_gap
from modules.helpers import buffer, print_lg

full_name = f"{first_name} {middle_name} {last_name}".replace("  ", " ").strip() if middle_name else f"{first_name} {last_name}"


MANUAL_APPLY_XPATHS = [
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply manually')]",
    ".//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply manually')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'manual apply')]",
    ".//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'manual apply')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply on company')]",
    ".//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply on company')]",
    ".//span[normalize-space(.)='Apply manually']/ancestor::button[1]",
    ".//span[normalize-space(.)='Apply manually']/ancestor::a[1]",
]

# Greenhouse / CareerPuck "Start Your Application" modal (inside iframe)
GREENHOUSE_START_MODAL_XPATHS = (
    ".//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start your application')]",
    ".//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'how would you like to apply')]",
)

AUTOFILL_RESUME_XPATHS = [
    ".//button[normalize-space(.)='Autofill with Resume']",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'autofill with resume')]",
    ".//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'autofill with resume')]",
]

APPLY_MANUALLY_MODAL_XPATHS = [
    ".//button[normalize-space(.)='Apply Manually']",
    ".//a[normalize-space(.)='Apply Manually']",
    ".//button[normalize-space(.)='Apply manually']",
    ".//a[normalize-space(.)='Apply manually']",
] + MANUAL_APPLY_XPATHS

# Workday / Greenhouse / Phenom — start application from job posting page
LANDING_APPLY_XPATHS = [
    "//button[@data-automation-id='jobPostingApplyButton']",
    "//a[@data-automation-id='applyButton']",
    "//button[@data-automation-id='applyButton']",
    "//button[@data-automation-id='adventureButton']",
    "#apply-button",
    "a#apply-button",
    "button#apply-button",
    ".//button[contains(@class,'postings-btn')]",
    ".//a[contains(@class,'postings-btn')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply for this job')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
    ".//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply for this job')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply for this role')]",
    ".//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply for this role')]",
    "a[href*='boards.greenhouse.io']",
    "a[href*='gh_jid']",
    "a[href*='/apply']",
    "[data-testid='apply-button']",
    "button[data-testid='apply-button']",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
    ".//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
    ".//button[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
    ".//a[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
    "button.apply-button",
    "a.apply-button",
    ".btn-apply",
    "[class*='apply-button']",
    "[class*='ApplyButton']",
]

NEXT_BUTTON_XPATHS = [
    "//button[@data-automation-id='bottom-navigation-next-button']",
    "//button[@data-automation-id='nextButton']",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'save and continue')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
]

SUBMIT_BUTTON_XPATHS = [
    "#submit_app",
    "input#submit_app",
    "button#submit_app",
    "button.ashby-application-form-submit-button",
    ".ashby-application-form-submit-button",
    "//button[@data-automation-id='submitButton']",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit application')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
    ".//input[@type='submit']",
]

SUCCESS_TEXT_MARKERS = (
    'thank you for applying', 'application submitted', 'application received',
    'thanks for applying', 'successfully submitted', 'we received your application',
)

ERROR_SELECTORS = (
    '.ashby-application-form-failure-container',
    '[role="alert"]',
    '.error-message',
    '.field-error',
    '.validation-error',
    '[class*="FieldError"]',
    '[class*="field-error"]',
    '[data-testid*="error"]',
)

_resume_uploaded_keys: set[str] = set()
_session_form_opened: bool = False

DROPDOWN_FIELD_SELECTORS = '.field, .application-field, .application-question, .question, [class*="field-wrapper"]'
DROPDOWN_CONTROL_SELECTORS = '.select__control, [role="combobox"], .select-shell, .dropdown-toggle, button[aria-haspopup="listbox"]'
DROPDOWN_OPTION_SELECTORS = "[role='option'], .select__option, [class*='select__option'], li[role='option']"

COOKIE_BUTTON_XPATHS = [
    "#onetrust-accept-btn-handler",
    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
    "#CybotCookiebotDialogBodyButtonAccept",
    "button[data-testid='cookie-policy-accept-all']",
    "button[data-testid='accept-cookies']",
    ".cc-accept",
    ".cc-allow",
    ".cc-dismiss",
    ".osano-cm-accept-all",
    ".truste-button1",
    "button[action-type='ACCEPT']",
    ".//button[contains(@class,'accept') and contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'cookie')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept cookies')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept and close')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow all')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow cookies')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree and continue')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i agree')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'got it')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'understood')]",
    ".//button[normalize-space(.)='Accept']",
    ".//button[normalize-space(.)='OK']",
    ".//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]",
    ".//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept cookies')]",
    ".//*[@role='button' and contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]",
    ".//*[@role='button' and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
]

COOKIE_REJECT_TEXT = (
    'decline', 'reject', 'deny', 'manage', 'settings', 'preferences',
    'only necessary', 'essential only', 'opt out', 'do not sell',
)

SKIP_BUTTON_TEXT = (
    'sign in', 'log in', 'login', 'register', 'create account', 'search',
)


def _page_fingerprint(driver: WebDriver) -> str:
    try:
        return (driver.find_element(By.TAG_NAME, 'body').text or '')[:4000]
    except Exception:
        return ''


def _wait_for_page(driver: WebDriver, timeout: float = 8) -> None:
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        buffer(1)
        accept_cookies_if_present(driver, quiet=True)
    except Exception:
        pass


def _get_label_for_element(element) -> str:
    try:
        eid = element.get_attribute('id')
        if eid:
            for label in element.find_elements(By.XPATH, f"//label[@for='{eid}']"):
                text = (label.text or '').replace('*', '').strip()
                if text:
                    return text
    except Exception:
        pass
    for xpath in (
        "./ancestor::div[contains(@class,'field')][1]//label",
        "./ancestor::div[contains(@class,'application-field')][1]//label",
        "./ancestor::div[contains(@class,'question')][1]//label",
        "./ancestor::label[1]",
        "./preceding::label[1]",
    ):
        try:
            label = element.find_element(By.XPATH, xpath)
            text = (label.text or '').replace('*', '').strip()
            if text and len(text) > 2:
                return text
        except Exception:
            continue
    return ''


def _field_context(element) -> str:
    parts = []
    for attr in ('aria-label', 'placeholder', 'name', 'id', 'autocomplete'):
        value = (element.get_attribute(attr) or '').strip()
        if value:
            parts.append(value)
    label = _get_label_for_element(element)
    if label:
        parts.append(label)
    try:
        parent = element.find_element(By.XPATH, "./ancestor::label[1]")
        if parent.text.strip():
            parts.append(parent.text.strip())
    except Exception:
        pass
    return ' '.join(parts).lower()


def _answer_for_label(label: str, work_location: str) -> str:
    label_low = label.lower()
    if 'linkedin' in label_low:
        return linkedIn
    if 'sponsor' in label_low or 'sponsorship' in label_low or ('require' in label_low and 'visa' in label_low):
        return require_visa
    if 'authorized' in label_low and 'work' in label_low:
        return 'Yes'
    if 'eligible' in label_low and 'work' in label_low:
        return 'Yes'
    if 'located' in label_low and 'canada' in label_low:
        return 'Yes' if country.lower() == 'canada' else 'No'
    if 'currently in' in label_low or 'currently located' in label_low:
        if 'canada' in label_low:
            return 'Yes' if country.lower() == 'canada' else 'No'
        if 'united states' in label_low or ' u.s.' in label_low or ' usa' in label_low:
            return 'Yes' if 'u.s.' in us_citizenship.lower() or 'citizen' in us_citizenship.lower() else 'No'
    if 'citizenship' in label_low or 'employment eligibility' in label_low:
        return us_citizenship if us_citizenship else 'Canadian Citizen/Permanent Resident'
    if 'gender' in label_low or 'sex' in label_low:
        return gender
    if 'disability' in label_low or 'handicapped' in label_low:
        return disability_status
    if 'veteran' in label_low:
        return veteran_status
    if any(word in label_low for word in ('location', 'city', 'where are you')) and 'located' not in label_low:
        if 'country' in label_low:
            return country
        if 'state' in label_low or 'province' in label_low:
            return state
        if 'city' in label_low:
            return current_city if current_city else work_location
        return current_city if current_city else work_location
    return _answer_for_context(label_low, work_location)


def _answer_candidates(answer: str) -> list[str]:
    candidates = [answer]
    low = answer.lower().strip()
    if low == 'yes':
        candidates.extend(['Yes', 'I am', 'Agree'])
    elif low == 'no':
        candidates.extend(['No', 'I am not', 'I do not'])
    elif 'yes' in low:
        candidates.append('Yes')
    elif 'no' in low:
        candidates.append('No')
    elif 'citizen' in low or 'resident' in low:
        candidates.extend(['Yes', 'No', answer])
    deduped = []
    for item in candidates:
        if item and item not in deduped:
            deduped.append(item)
    return deduped


def _option_matches(candidate: str, option_text: str) -> bool:
    c = candidate.lower().strip()
    o = option_text.lower().strip()
    if not c or not o:
        return False
    if c == o or c in o or o in c:
        return True
    if c.startswith('y') and o.startswith('yes'):
        return True
    if c.startswith('n') and (o == 'no' or o.startswith('no')):
        return True
    return False


def _dropdown_needs_fill(container) -> bool:
    try:
        text = (container.text or '').lower()
        if any(token in text for token in ('select...', 'select an option', 'choose an option', 'please select')):
            return True
        for ph in container.find_elements(By.CSS_SELECTOR, '.select__placeholder, [class*="placeholder"]'):
            if ph.is_displayed():
                return True
    except Exception:
        pass
    return False


def _label_for_container(container) -> str:
    for selector in ('label', '.label', 'legend'):
        for el in container.find_elements(By.CSS_SELECTOR, selector):
            text = (el.text or '').replace('*', '').strip()
            if text and len(text) > 2:
                return text
    return _get_label_for_element(container)


def _click_and_select_option(driver: WebDriver, control, answer: str, label: str = '') -> bool:
    if not answer:
        return False
    candidates = _answer_candidates(answer)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", control)
    buffer(click_gap)
    try:
        control.click()
    except (ElementClickInterceptedException, ElementNotInteractableException):
        driver.execute_script("arguments[0].click();", control)
    buffer(click_gap)

    try:
        WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, DROPDOWN_OPTION_SELECTORS))
        )
    except Exception:
        pass

    options = driver.find_elements(By.CSS_SELECTOR, DROPDOWN_OPTION_SELECTORS)
    for candidate in candidates:
        for opt in options:
            try:
                if not opt.is_displayed():
                    continue
                opt_text = (opt.text or opt.get_attribute('textContent') or '').strip()
                if _option_matches(candidate, opt_text):
                    try:
                        opt.click()
                    except (ElementClickInterceptedException, ElementNotInteractableException):
                        driver.execute_script("arguments[0].click();", opt)
                    buffer(click_gap)
                    print_lg(f'Selected "{opt_text}" for "{label or answer}"')
                    return True
            except StaleElementReferenceException:
                continue

    try:
        search_input = driver.switch_to.active_element
        if search_input.tag_name.lower() == 'input':
            for candidate in candidates:
                search_input.clear()
                search_input.send_keys(candidate)
                buffer(0.5)
                options = driver.find_elements(By.CSS_SELECTOR, DROPDOWN_OPTION_SELECTORS)
                for opt in options:
                    if opt.is_displayed() and _option_matches(candidate, (opt.text or '').strip()):
                        opt.click()
                        buffer(click_gap)
                        print_lg(f'Selected "{opt.text.strip()}" for "{label or answer}" (typed search)')
                        return True
    except Exception:
        pass
    return False


def _fill_custom_dropdowns(driver: WebDriver, work_location: str) -> int:
    filled = 0
    seen = set()
    for selector in DROPDOWN_FIELD_SELECTORS.split(', '):
        for field in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if not field.is_displayed():
                    continue
                field_key = field.id or field.get_attribute('outerHTML')[:100]
                if field_key in seen:
                    continue
                if not _dropdown_needs_fill(field):
                    continue
                label = _label_for_container(field)
                if not label:
                    continue
                answer = _answer_for_label(label, work_location)
                if not answer:
                    continue
                for sel in field.find_elements(By.TAG_NAME, 'select'):
                    if sel.is_displayed() or sel.get_attribute('aria-hidden') != 'true':
                        _fill_select(sel, label.lower(), work_location)
                        filled += 1
                        seen.add(field_key)
                        break
                else:
                    control = None
                    for ctrl_sel in DROPDOWN_CONTROL_SELECTORS.split(', '):
                        found = field.find_elements(By.CSS_SELECTOR, ctrl_sel)
                        if found:
                            control = found[0]
                            break
                    if control and _click_and_select_option(driver, control, answer, label):
                        filled += 1
                        seen.add(field_key)
            except StaleElementReferenceException:
                continue
            except Exception:
                continue
    return filled


def _count_unfilled_custom_dropdowns(driver: WebDriver) -> int:
    count = 0
    seen = set()
    for selector in DROPDOWN_FIELD_SELECTORS.split(', '):
        for field in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                key = field.id or field.get_attribute('outerHTML')[:100]
                if key in seen:
                    continue
                seen.add(key)
                if field.is_displayed() and _dropdown_needs_fill(field):
                    count += 1
            except Exception:
                continue
    return count


def _answer_for_context(context: str, work_location: str) -> str:
    if not context:
        return ''
    if 'email' in context:
        return email
    if 'phone' in context or 'mobile' in context or 'tel' in context:
        return phone_number
    if 'first' in context and 'name' in context and 'last' not in context:
        return first_name
    if 'last' in context and 'name' in context:
        return last_name
    if 'full' in context and 'name' in context:
        return full_name
    if 'name' in context and 'company' not in context and 'employer' not in context:
        return full_name
    if 'linkedin' in context:
        return linkedIn
    if 'website' in context or 'portfolio' in context or 'github' in context:
        return website
    if 'street' in context or 'address line' in context:
        return street
    if 'city' in context or 'location' in context:
        return current_city if current_city else work_location
    if 'state' in context or 'province' in context:
        return state
    if 'zip' in context or 'postal' in context:
        return zipcode
    if 'country' in context:
        return country
    if 'experience' in context or 'years' in context:
        return years_of_experience
    if 'sponsor' in context or 'visa' in context:
        return require_visa
    if 'authorized' in context and 'work' in context:
        return 'Yes'
    if 'located' in context and 'canada' in context:
        return 'Yes' if country.lower() == 'canada' else 'No'
    if 'currently located' in context or 'currently in' in context:
        if 'canada' in context:
            return 'Yes' if country.lower() == 'canada' else 'No'
    if 'citizenship' in context or 'authorized' in context or 'eligible to work' in context:
        if 'canada' in context:
            return 'Yes'
        return us_citizenship if us_citizenship else 'Canadian Citizen/Permanent Resident'
    if 'salary' in context or 'compensation' in context or 'ctc' in context:
        return str(desired_salary)
    if 'notice' in context:
        return str(notice_period)
    if 'headline' in context:
        return linkedin_headline
    if 'cover' in context:
        return cover_letter.strip()
    if 'summary' in context or 'about you' in context:
        return linkedin_summary.strip()
    if 'employer' in context:
        return recent_employer
    return ''


def _field_value(element) -> str:
    tag = element.tag_name.lower()
    if tag == 'select':
        try:
            return (Select(element).first_selected_option.text or '').strip()
        except Exception:
            return ''
    return (element.get_attribute('value') or '').strip()


def _is_required_unanswered(element) -> bool:
    try:
        if not element.is_displayed() or not element.is_enabled():
            return False
        required = element.get_attribute('required') is not None or element.get_attribute('aria-required') == 'true'
        if not required:
            context = _field_context(element)
            if not any(word in context for word in ('email', 'phone', 'name', 'resume', 'cv')):
                return False
            if 'email' in context and not _field_value(element):
                return True
            if ('phone' in context or 'mobile' in context) and not _field_value(element):
                return True
            if 'name' in context and 'company' not in context and not _field_value(element):
                return True
            return False
        value = _field_value(element)
        if element.tag_name.lower() == 'select':
            return value.lower() in ('', 'select', 'select an option', 'choose', 'please select')
        return not value
    except Exception:
        return False


def _count_unanswered_required(driver: WebDriver) -> int:
    count = 0
    selectors = [
        "input:not([type='hidden']):not([type='submit']):not([type='button']):not([type='checkbox']):not([type='radio']):not([type='file'])",
        "select",
        "textarea",
    ]
    seen = set()
    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                key = element.id or element.get_attribute('name') or element.get_attribute('outerHTML')[:80]
                if key in seen:
                    continue
                seen.add(key)
                if _is_required_unanswered(element):
                    count += 1
            except StaleElementReferenceException:
                continue
    return count


def _fill_text_input(element, answer: str) -> None:
    if not answer:
        return
    try:
        element.clear()
    except Exception:
        pass
    element.send_keys(answer)


def _fill_select(element, context: str, work_location: str) -> None:
    select = Select(element)
    selected = (select.first_selected_option.text or '').strip().lower()
    if selected and selected not in ('', 'select', 'select an option', 'choose', 'please select', 'select...'):
        return
    answer = _answer_for_label(context, work_location) if len(context) > 15 else _answer_for_context(context, work_location)
    options = [option.text for option in select.options if option.text.strip()]
    if not options:
        return
    candidates = []
    if answer:
        candidates.append(answer)
    if 'sponsor' in context or 'visa' in context:
        candidates.extend([require_visa, 'No', 'Yes'])
    if 'country' in context:
        candidates.append(country)
    if 'gender' in context:
        candidates.append(gender)
    if 'disability' in context:
        candidates.append(disability_status)
    if 'veteran' in context:
        candidates.append(veteran_status)
    for candidate in candidates:
        for option in options:
            if _option_matches(candidate, option):
                select.select_by_visible_text(option)
                return


def _upload_resume_if_needed(driver: WebDriver, resume_path: str) -> bool:
    global _resume_uploaded_keys
    if not resume_path or not os.path.isfile(resume_path):
        return False
    uploaded = False
    for inp in driver.find_elements(By.CSS_SELECTOR, "input[type='file']"):
        try:
            key = inp.id or inp.get_attribute('name') or inp.get_attribute('outerHTML')[:100]
            if key in _resume_uploaded_keys:
                continue
            existing = (inp.get_attribute('value') or '').strip()
            if existing:
                _resume_uploaded_keys.add(key)
                continue
            context = _field_context(inp)
            if uploaded and 'resume' not in context and 'cv' not in context and 'cover' not in context:
                continue
            inp.send_keys(os.path.abspath(resume_path))
            _resume_uploaded_keys.add(key)
            uploaded = True
            print_lg(f'Uploaded resume on external form: {os.path.basename(resume_path)}')
            buffer(click_gap)
        except Exception:
            continue
    return uploaded


def _fill_ashby_fields(driver: WebDriver, work_location: str) -> int:
    if 'ashbyhq.com' not in (driver.current_url or ''):
        return 0
    filled = 0
    for entry in driver.find_elements(By.CSS_SELECTOR, '.ashby-application-form-field-entry'):
        try:
            if not entry.is_displayed():
                continue
            title_els = entry.find_elements(By.CSS_SELECTOR, '.ashby-application-form-question-title')
            if not title_els:
                continue
            title = title_els[0].text.replace('*', '').strip()
            if not title:
                continue
            answer = _answer_for_label(title, work_location)
            if not answer:
                continue

            answered = False
            for btn in entry.find_elements(By.CSS_SELECTOR, 'button'):
                try:
                    if not btn.is_displayed():
                        continue
                    btn_text = (btn.text or btn.get_attribute('aria-label') or '').strip()
                    if _option_matches(answer, btn_text):
                        btn.click()
                        buffer(click_gap)
                        print_lg(f'Ashby: selected "{btn_text}" for "{title}"')
                        filled += 1
                        answered = True
                        break
                except Exception:
                    continue
            if answered:
                continue

            for ctrl in entry.find_elements(By.CSS_SELECTOR, '[role="combobox"], button[aria-haspopup="listbox"], select'):
                if _click_and_select_option(driver, ctrl, answer, title):
                    filled += 1
                    break
            else:
                for inp in entry.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']):not([type='file']), textarea"):
                    try:
                        if not inp.is_displayed() or (inp.get_attribute('value') or '').strip():
                            continue
                        ans = _answer_for_context(_field_context(inp) or title.lower(), work_location) or answer
                        if ans:
                            _fill_text_input(inp, ans)
                            filled += 1
                    except Exception:
                        continue
        except StaleElementReferenceException:
            continue
        except Exception:
            continue
    return filled


def _fill_all_fields(driver: WebDriver, work_location: str) -> int:
    return _fill_page_fields(driver, work_location) + _fill_ashby_fields(driver, work_location)


def _read_validation_errors(driver: WebDriver) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()

    for selector in ERROR_SELECTORS:
        for el in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if not el.is_displayed():
                    continue
                text = ' '.join((el.text or '').split())
                if not text or len(text) < 3 or text in seen:
                    continue
                low = text.lower()
                if any(skip in low for skip in ('cookie', 'sign in', 'log in')):
                    continue
                seen.add(text)
                errors.append(text[:250])
            except Exception:
                continue

    for entry in driver.find_elements(By.CSS_SELECTOR, '.ashby-application-form-field-entry'):
        try:
            if not entry.is_displayed():
                continue
            invalid = entry.find_elements(By.CSS_SELECTOR, '[aria-invalid="true"], [class*="error"], [class*="Error"]')
            if not invalid:
                continue
            title_els = entry.find_elements(By.CSS_SELECTOR, '.ashby-application-form-question-title')
            title = title_els[0].text.replace('*', '').strip() if title_els else 'Unknown field'
            msg = f'Missing or invalid: {title}'
            if msg not in seen:
                seen.add(msg)
                errors.append(msg)
        except Exception:
            continue

    for el in driver.find_elements(By.CSS_SELECTOR, '[aria-invalid="true"]'):
        try:
            if not el.is_displayed():
                continue
            label = _get_label_for_element(el) or _field_context(el)
            if label:
                msg = f'Missing or invalid: {label[:120]}'
                if msg not in seen:
                    seen.add(msg)
                    errors.append(msg)
        except Exception:
            continue

    return errors


def _submit_success_visible(driver: WebDriver) -> bool:
    try:
        for el in driver.find_elements(By.CSS_SELECTOR, '.ashby-application-form-success-container'):
            if el.is_displayed() and (el.text or '').strip():
                return True
        body = (driver.find_element(By.TAG_NAME, 'body').text or '').lower()
        if any(marker in body for marker in SUCCESS_TEXT_MARKERS):
            return True
    except Exception:
        pass
    return False


def _submit_form_still_open(driver: WebDriver) -> bool:
    try:
        for selector in SUBMIT_BUTTON_XPATHS:
            if selector.startswith('.') or selector.startswith('//'):
                elements = driver.find_elements(By.XPATH, selector)
            else:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                if el.is_displayed() and el.is_enabled():
                    return True
    except Exception:
        pass
    return False


def _verify_submit_result(driver: WebDriver) -> tuple[bool, list[str]]:
    buffer(2)
    errors = _read_validation_errors(driver)
    if _submit_success_visible(driver) and not errors:
        return True, []
    if errors:
        return False, errors
    if _submit_form_still_open(driver):
        unfilled = _describe_unfilled_fields(driver)
        if unfilled:
            return False, [f'Form still open — unfilled: {", ".join(unfilled)}']
        return False, ['Form still open after submit — validation may have failed']
    return True, []


def _retry_fill_from_errors(driver: WebDriver, work_location: str, errors: list[str]) -> int:
    filled = _fill_all_fields(driver, work_location)
    error_blob = ' '.join(errors).lower()
    for entry in driver.find_elements(By.CSS_SELECTOR, '.ashby-application-form-field-entry'):
        try:
            title_els = entry.find_elements(By.CSS_SELECTOR, '.ashby-application-form-question-title')
            if not title_els:
                continue
            title = title_els[0].text.replace('*', '').strip()
            if not title:
                continue
            if title.lower() not in error_blob and f'missing or invalid: {title.lower()}' not in error_blob:
                if not any(part in error_blob for part in title.lower().split()[:4]):
                    continue
            answer = _answer_for_label(title, work_location)
            if not answer:
                continue
            for btn in entry.find_elements(By.CSS_SELECTOR, 'button'):
                if btn.is_displayed() and _option_matches(answer, (btn.text or '').strip()):
                    btn.click()
                    buffer(click_gap)
                    print_lg(f'Fixed Ashby field after error: "{title}" → "{btn.text.strip()}"')
                    filled += 1
                    break
            else:
                for ctrl in entry.find_elements(By.CSS_SELECTOR, '[role="combobox"], button[aria-haspopup="listbox"]'):
                    if _click_and_select_option(driver, ctrl, answer, title):
                        filled += 1
                        break
        except Exception:
            continue
    return filled


def _attempt_submit_with_fixes(driver: WebDriver, work_location: str, resume_path: str, max_attempts: int = 3) -> tuple[bool, str]:
    last_reason = 'Submit not attempted'
    for attempt in range(1, max_attempts + 1):
        _upload_resume_if_needed(driver, resume_path)
        filled = _fill_all_fields(driver, work_location)
        if filled:
            print_lg(f'Filled {filled} field(s) on external form (attempt {attempt}).')

        pre_errors = _read_validation_errors(driver)
        if pre_errors:
            print_lg(f'Validation messages on form: {"; ".join(pre_errors[:3])}')
            _retry_fill_from_errors(driver, work_location, pre_errors)

        unanswered = _count_unanswered_required(driver) + _count_unfilled_custom_dropdowns(driver)
        if unanswered:
            unfilled = _describe_unfilled_fields(driver)
            print_lg(f'{unanswered} required field(s) empty before submit: {", ".join(unfilled) if unfilled else unanswered}')

        if not _click_button(driver, SUBMIT_BUTTON_XPATHS):
            return False, 'Submit button not found or not clickable'

        print_lg(f'Clicked Submit on external application form (attempt {attempt}/{max_attempts}).')
        ok, post_errors = _verify_submit_result(driver)
        if ok:
            print_lg('Submission confirmed on page.')
            return True, 'Submitted successfully'

        last_reason = '; '.join(post_errors) if post_errors else 'Submit did not complete'
        print_lg(f'Submit not accepted — {last_reason}')
        if post_errors:
            fixed = _retry_fill_from_errors(driver, work_location, post_errors)
            if fixed:
                print_lg(f'Re-filled {fixed} field(s) after validation error.')
        buffer(2)

    return False, f'Submit failed after {max_attempts} attempts: {last_reason}'


def _fill_page_fields(driver: WebDriver, work_location: str) -> int:
    filled = 0
    selectors = [
        "input:not([type='hidden']):not([type='submit']):not([type='button']):not([type='checkbox']):not([type='radio']):not([type='file'])",
        "select",
        "textarea",
    ]
    seen = set()
    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if not element.is_displayed() or not element.is_enabled():
                    continue
                key = element.id or element.get_attribute('outerHTML')[:120]
                if key in seen:
                    continue
                seen.add(key)
                context = _field_context(element)
                tag = element.tag_name.lower()
                input_type = (element.get_attribute('type') or '').lower()
                if tag == 'select':
                    _fill_select(element, context, work_location)
                    filled += 1
                elif tag == 'textarea':
                    answer = _answer_for_context(context, work_location)
                    if answer:
                        _fill_text_input(element, answer)
                        filled += 1
                elif input_type == 'email':
                    _fill_text_input(element, email)
                    filled += 1
                else:
                    answer = _answer_for_context(context, work_location)
                    if answer:
                        _fill_text_input(element, answer)
                        filled += 1
            except StaleElementReferenceException:
                continue
            except Exception:
                continue
    filled += _fill_custom_dropdowns(driver, work_location)
    return filled


def _click_button(driver: WebDriver, xpaths: list[str]) -> bool:
    for xpath in xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath) if xpath.startswith('.') or xpath.startswith('//') else driver.find_elements(By.CSS_SELECTOR, xpath)
        except Exception:
            elements = []
        for btn in elements:
            try:
                if not btn.is_displayed() or not btn.is_enabled():
                    continue
                text = (btn.text or btn.get_attribute('value') or btn.get_attribute('aria-label') or '').lower()
                if any(skip in text for skip in SKIP_BUTTON_TEXT):
                    continue
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                buffer(click_gap)
                try:
                    btn.click()
                except (ElementClickInterceptedException, ElementNotInteractableException):
                    driver.execute_script("arguments[0].click();", btn)
                buffer(click_gap)
                return True
            except Exception:
                continue
    return False


def _cookie_button_text(element) -> str:
    return ' '.join(filter(None, [
        (element.text or '').strip(),
        (element.get_attribute('value') or '').strip(),
        (element.get_attribute('aria-label') or '').strip(),
        (element.get_attribute('title') or '').strip(),
    ])).lower()


def _is_cookie_reject_button(text: str) -> bool:
    return any(reject in text for reject in COOKIE_REJECT_TEXT)


def _click_cookie_button(driver: WebDriver) -> bool:
    for xpath in COOKIE_BUTTON_XPATHS:
        try:
            if xpath.startswith('.') or xpath.startswith('//'):
                elements = driver.find_elements(By.XPATH, xpath)
            else:
                elements = driver.find_elements(By.CSS_SELECTOR, xpath)
        except Exception:
            elements = []
        for btn in elements:
            try:
                if not btn.is_displayed() or not btn.is_enabled():
                    continue
                text = _cookie_button_text(btn)
                if text and _is_cookie_reject_button(text):
                    continue
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                buffer(click_gap)
                try:
                    btn.click()
                except (ElementClickInterceptedException, ElementNotInteractableException):
                    driver.execute_script("arguments[0].click();", btn)
                buffer(click_gap)
                return True
            except Exception:
                continue
    return False


def accept_cookies_if_present(driver: WebDriver, quiet: bool = False) -> bool:
    '''
    Accept cookie consent banners on the current page, including common iframe-based CMPs.
    '''
    try:
        if _click_cookie_button(driver):
            if not quiet:
                print_lg('Accepted cookie consent banner.')
            buffer(1)
            return True

        iframes = driver.find_elements(By.TAG_NAME, 'iframe')[:8]
        for iframe in iframes:
            try:
                iframe_id = (iframe.get_attribute('id') or '').lower()
                iframe_name = (iframe.get_attribute('name') or '').lower()
                iframe_title = (iframe.get_attribute('title') or '').lower()
                if not any(token in f'{iframe_id} {iframe_name} {iframe_title}' for token in (
                    'cookie', 'consent', 'onetrust', 'sp_message', 'privacy', 'gdpr', 'trustarc', 'osano',
                )):
                    continue
                driver.switch_to.frame(iframe)
                if _click_cookie_button(driver):
                    driver.switch_to.default_content()
                    if not quiet:
                        print_lg('Accepted cookie consent banner (iframe).')
                    buffer(1)
                    return True
            except WebDriverException:
                pass
            finally:
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass

        for iframe in iframes[:3]:
            try:
                driver.switch_to.frame(iframe)
                if _click_cookie_button(driver):
                    driver.switch_to.default_content()
                    if not quiet:
                        print_lg('Accepted cookie consent banner (iframe).')
                    buffer(1)
                    return True
            except WebDriverException:
                pass
            finally:
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass
    except WebDriverException:
        pass
    return False


def _dismiss_cookie_banners(driver: WebDriver) -> None:
    accept_cookies_if_present(driver)


def _application_start_modal_visible(driver: WebDriver) -> bool:
    try:
        for xpath in GREENHOUSE_START_MODAL_XPATHS:
            for el in driver.find_elements(By.XPATH, xpath):
                if el.is_displayed():
                    return True
        body = (driver.find_element(By.TAG_NAME, 'body').text or '').lower()
        if 'start your application' in body and 'apply manually' in body:
            return True
    except Exception:
        pass
    return False


def _handle_application_start_modal(driver: WebDriver) -> bool:
    '''
    Greenhouse embed shows "Start Your Application" with Apply Manually / Autofill with Resume.
    Must click through before the real form appears.
    '''
    modal_visible = _application_start_modal_visible(driver)
    apply_btn_visible = False
    try:
        for xpath in APPLY_MANUALLY_MODAL_XPATHS[:4]:
            for el in driver.find_elements(By.XPATH, xpath):
                if el.is_displayed():
                    apply_btn_visible = True
                    break
            if apply_btn_visible:
                break
    except Exception:
        pass

    if not modal_visible and not apply_btn_visible:
        return False

    if _click_button(driver, APPLY_MANUALLY_MODAL_XPATHS):
        print_lg('Clicked "Apply Manually" on Start Your Application modal.')
        buffer(2)
        return True
    if _click_button(driver, AUTOFILL_RESUME_XPATHS):
        print_lg('Clicked "Autofill with Resume" on Start Your Application modal.')
        buffer(2)
        return True
    return False


def click_apply_manually_if_present(driver: WebDriver, linkedin_only: bool = True) -> bool:
    '''Only use on LinkedIn apply dialogs — not on company career sites.'''
    if linkedin_only and 'linkedin.com' not in (driver.current_url or '').lower():
        return False
    if _click_button(driver, MANUAL_APPLY_XPATHS):
        print_lg('Clicked "Apply manually" option.')
        buffer(click_gap)
        return True
    return False


def _form_state_fingerprint(driver: WebDriver) -> str:
    try:
        unfilled = _count_unanswered_required(driver) + _count_unfilled_custom_dropdowns(driver)
        url = driver.current_url
        inputs = len(driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']), select, textarea"))
        return f'{url}|{unfilled}|{inputs}'
    except Exception:
        return _page_fingerprint(driver)


def _has_visible_form_fields(driver: WebDriver) -> bool:
    try:
        return len(driver.find_elements(
            By.CSS_SELECTOR,
            "input:not([type='hidden']), select, textarea, [role='combobox'], input[type='file']",
        )) > 0
    except Exception:
        return False


def _switch_to_application_frame(driver: WebDriver, quiet: bool = False) -> bool:
    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    frame_tokens = (
        'greenhouse', 'grnhse', 'apply', 'job-board', 'gem.com', 'workday', 'application',
        'phenom', 'eightfold', 'icims', 'taleo', 'mongodb', 'careers', 'brassring',
        'careerpuck',
    )

    def _try_frame(iframe) -> bool:
        try:
            src = (iframe.get_attribute('src') or '').lower()
            title = (iframe.get_attribute('title') or '').lower()
            name = (iframe.get_attribute('name') or '').lower()
            blob = f'{src} {title} {name}'
            if not any(token in blob for token in frame_tokens):
                return False
            driver.switch_to.frame(iframe)
            buffer(1)
            if not quiet:
                print_lg('Switched to embedded application iframe.')
            return True
        except Exception:
            return False

    for iframe in driver.find_elements(By.TAG_NAME, 'iframe'):
        if _try_frame(iframe):
            return True

    for outer in driver.find_elements(By.TAG_NAME, 'iframe'):
        try:
            driver.switch_to.default_content()
            driver.switch_to.frame(outer)
            for inner in driver.find_elements(By.TAG_NAME, 'iframe'):
                if _try_frame(inner):
                    return True
            if _has_visible_form_fields(driver):
                if not quiet:
                    print_lg('Using outer iframe with form fields.')
                return True
        except Exception:
            pass
    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    return False


def _start_application_in_frame(driver: WebDriver) -> bool:
    if _has_visible_form_fields(driver):
        return False
    _dismiss_cookie_banners(driver)
    if _handle_application_start_modal(driver):
        return True
    if _click_button(driver, LANDING_APPLY_XPATHS):
        print_lg('Clicked Apply inside application iframe.')
        buffer(2)
        if _handle_application_start_modal(driver):
            return True
        return True
    return _handle_application_start_modal(driver)


def _focus_application_context(driver: WebDriver) -> bool:
    '''Re-enter the application iframe without re-clicking Apply on the landing page.'''
    if _has_visible_form_fields(driver):
        return True
    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    if _switch_to_application_frame(driver, quiet=True):
        if _handle_application_start_modal(driver):
            buffer(1)
        if _has_visible_form_fields(driver):
            return True
    if _handle_application_start_modal(driver):
        buffer(1)
    return _has_visible_form_fields(driver)


def _ensure_application_form_open(driver: WebDriver) -> bool:
    global _session_form_opened
    if _session_form_opened:
        return _focus_application_context(driver)

    try:
        driver.switch_to.default_content()
    except Exception:
        pass

    platform = _detect_ats_platform(driver)
    if platform != 'Unknown':
        print_lg(f'ATS platform detected: {platform}')

    _start_application_on_landing_page(driver)
    buffer(2)

    if _switch_to_application_frame(driver):
        _start_application_in_frame(driver)
        _handle_application_start_modal(driver)
        buffer(1)

    if _wait_for_form_fields(driver, 10):
        _session_form_opened = True
        return True

    # One retry: iframe may load slowly (CareerPuck / Greenhouse embed)
    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    buffer(2)
    if _switch_to_application_frame(driver, quiet=True):
        _start_application_in_frame(driver)
        _handle_application_start_modal(driver)
    if _wait_for_form_fields(driver, 8):
        _session_form_opened = True
        return True

    if _has_visible_form_fields(driver):
        _session_form_opened = True
        return True
    return False


def _detect_ats_platform(driver: WebDriver) -> str:
    try:
        url = (driver.current_url or '').lower()
        if 'dayforcehcm.com' in url or 'dayforce' in url:
            return 'Dayforce'
        if 'greenhouse.io' in url or 'gh_jid' in url or 'gh_src' in url:
            return 'Greenhouse'
        if 'myworkdayjobs.com' in url or 'workday' in url:
            return 'Workday'
        if 'jobs.gem.com' in url or 'gem.com' in url:
            return 'Gem'
        if 'lever.co' in url:
            return 'Lever'
        if 'smartrecruiters.com' in url:
            return 'SmartRecruiters'
        if 'stripe.com/jobs' in url:
            return 'Stripe/Greenhouse'
        if 'rsmus.com' in url or 'jobs.rsm' in url:
            return 'RSM/Phenom'
        if 'mongodb.com' in url:
            return 'MongoDB/Phenom'
        if 'ashbyhq.com' in url:
            return 'Ashby'
        if 'careerpuck.com' in url:
            return 'Greenhouse/CareerPuck'
        if 'phenom' in url or 'eightfold' in url:
            return 'Phenom/Eightfold'
    except Exception:
        pass
    return 'Unknown'


def _wait_for_form_fields(driver: WebDriver, timeout: float = 12) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(
                By.CSS_SELECTOR,
                "input:not([type='hidden']), select, textarea, [role='combobox'], input[type='file']",
            )) > 0
        )
        return True
    except Exception:
        return False


def _open_platform_application(driver: WebDriver) -> bool:
    url = (driver.current_url or '').lower()
    extra_xpaths = []
    if 'dayforcehcm.com' in url:
        extra_xpaths = [
            ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
            ".//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
            ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply for position')]",
            ".//a[contains(@href,'apply')]",
            "button[class*='apply']",
            "a[class*='apply']",
        ]
        print_lg('Detected Dayforce careers site — looking for Apply button.')
    elif 'jobs.gem.com' in url:
        extra_xpaths = [
            "[data-testid='apply-button']",
            "button[data-testid='apply-button']",
            ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
        ]
        print_lg('Detected Gem careers site — looking for Apply button.')
    elif 'mongodb.com' in url:
        extra_xpaths = [
            ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
            ".//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
            ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply for')]",
        ]
        print_lg('Detected MongoDB careers site — looking for Apply button.')
    if extra_xpaths and _click_button(driver, extra_xpaths):
        print_lg('Clicked platform-specific Apply button.')
        buffer(2)
        return True
    return False


def _start_application_on_landing_page(driver: WebDriver) -> bool:
    _dismiss_cookie_banners(driver)
    if _open_platform_application(driver):
        return True
    if _click_button(driver, LANDING_APPLY_XPATHS):
        print_lg('Clicked Apply on company job posting page.')
        buffer(2)
        return True
    return False


def try_linkedin_span_click(driver: WebDriver, text: str) -> bool:
    try:
        el = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, f'.//span[normalize-space(.)="{text}"]'))
        )
        el.click()
        buffer(click_gap)
        return True
    except Exception:
        return False


def switch_to_external_tab(driver: WebDriver, linkedIn_tab: str) -> bool:
    for handle in reversed(driver.window_handles):
        if handle != linkedIn_tab:
            driver.switch_to.window(handle)
            _wait_for_page(driver)
            return True
    return False


def is_linkedin_external_apply(driver: WebDriver) -> bool:
    try:
        for selector in (
            ".//button[contains(@class,'jobs-apply-button')]",
            ".//a[contains(@class,'jobs-apply-button')]",
        ):
            for btn in driver.find_elements(By.XPATH, selector):
                aria = (btn.get_attribute('aria-label') or '').lower()
                if 'easy apply' in aria and 'company website' not in aria:
                    continue
                if 'company website' in aria or ' on company' in aria:
                    return True
                if btn.tag_name.lower() == 'a':
                    href = (btn.get_attribute('href') or '').lower()
                    if href and 'openSDUIApplyFlow' not in href:
                        return True
    except Exception:
        pass
    return False


def _describe_unfilled_fields(driver: WebDriver, limit: int = 5) -> list[str]:
    labels = []
    seen = set()
    for selector in DROPDOWN_FIELD_SELECTORS.split(', '):
        for field in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if not field.is_displayed() or not _dropdown_needs_fill(field):
                    continue
                label = _label_for_container(field)
                if label and label not in seen:
                    seen.add(label)
                    labels.append(label)
            except Exception:
                continue
    for element in driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']), select, textarea"):
        try:
            if not _is_required_unanswered(element):
                continue
            label = _get_label_for_element(element) or _field_context(element)
            if label and label not in seen:
                seen.add(label)
                labels.append(label[:120])
        except Exception:
            continue
    return labels[:limit]


def _summarize_form_blockers(driver: WebDriver) -> str:
    details = []
    unanswered = _count_unanswered_required(driver) + _count_unfilled_custom_dropdowns(driver)
    if unanswered:
        unfilled_labels = _describe_unfilled_fields(driver)
        if unfilled_labels:
            details.append(f'{unanswered} required field(s) still empty: {", ".join(unfilled_labels)}')
        else:
            details.append(f'{unanswered} required field(s) still empty')
    try:
        input_count = len(driver.find_elements(
            By.CSS_SELECTOR,
            "input:not([type='hidden']), select, textarea, [role='combobox']",
        ))
        if input_count == 0:
            details.append('no application form fields detected on page')
    except Exception:
        pass
    return '; '.join(details)


def fill_and_submit_external_form(
    driver: WebDriver,
    work_location: str,
    job_description: str | None,
    resume_path: str,
    actions,
) -> tuple[bool, str, bool, str]:
    if not fill_external_application_forms:
        return False, 'External form fill disabled', True, 'External form fill disabled in config/search.py'

    print_lg(f'Filling external application form (max {external_apply_max_steps} Next clicks, tab stays open)...')
    global _resume_uploaded_keys, _session_form_opened
    _resume_uploaded_keys = set()
    _session_form_opened = False
    _wait_for_page(driver)
    if not _ensure_application_form_open(driver):
        print_lg('Could not open application form on first attempt — will keep trying during fill.')

    submitted = False
    next_clicks = 0
    unchanged_steps = 0
    stop_reason = ''
    last_error = ''

    while next_clicks < external_apply_max_steps:
        try:
            _focus_application_context(driver)
            _dismiss_cookie_banners(driver)
            _upload_resume_if_needed(driver, resume_path)
            state_before = _form_state_fingerprint(driver)
            filled = _fill_all_fields(driver, work_location)
            if filled:
                print_lg(f'Filled {filled} field(s) on external form.')
            elif next_clicks == 0 and not stop_reason:
                unanswered_now = _count_unanswered_required(driver) + _count_unfilled_custom_dropdowns(driver)
                if unanswered_now > 0:
                    unfilled = _describe_unfilled_fields(driver)
                    if unfilled:
                        stop_reason = f'Form found but could not auto-fill: {", ".join(unfilled)}'
                    else:
                        stop_reason = f'Form found but {unanswered_now} required field(s) could not be auto-filled'
                else:
                    stop_reason = 'Application form not found or no fillable fields on company site'

            if external_auto_submit and _submit_form_still_open(driver):
                ok, submit_reason = _attempt_submit_with_fixes(driver, work_location, resume_path)
                if ok:
                    submitted = True
                    stop_reason = submit_reason
                    break
                stop_reason = submit_reason
                print_lg(f'External apply incomplete — {submit_reason}')
                break

            if external_auto_submit and not _submit_form_still_open(driver) and _submit_success_visible(driver):
                submitted = True
                print_lg('Submission already confirmed on page.')
                break

            unanswered = _count_unanswered_required(driver) + _count_unfilled_custom_dropdowns(driver)
            if unanswered > 0 and (filled or next_clicks > 0):
                print_lg(f'{unanswered} required field(s) still empty — continuing to try Next/submit.')

            if not _click_button(driver, NEXT_BUTTON_XPATHS):
                if next_clicks == 0:
                    _focus_application_context(driver)
                    if not _click_button(driver, NEXT_BUTTON_XPATHS):
                        if unanswered == 0 and external_auto_submit and _submit_form_still_open(driver):
                            ok, submit_reason = _attempt_submit_with_fixes(driver, work_location, resume_path)
                            if ok:
                                submitted = True
                                stop_reason = submit_reason
                            else:
                                stop_reason = submit_reason or stop_reason
                        else:
                            stop_reason = stop_reason or 'No Apply/Next/Submit button found on company site'
                        break
                else:
                    stop_reason = stop_reason or 'No Next/Continue button found for next form step'
                    break

            next_clicks += 1
            buffer(2)
            print_lg(f'Clicked Next/Continue on external form ({next_clicks}/{external_apply_max_steps}).')

            state_after = _form_state_fingerprint(driver)
            if state_before == state_after:
                unchanged_steps += 1
                if unchanged_steps >= external_apply_max_steps:
                    stop_reason = f'Form did not advance after {unchanged_steps} Next clicks (same step/URL)'
                    print_lg(f'{stop_reason} — stopping.')
                    break
            else:
                unchanged_steps = 0
        except Exception as e:
            last_error = str(e)
            stop_reason = f'External form error: {last_error}'
            print_lg(stop_reason)
            break

    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    _focus_application_context(driver)
    _fill_all_fields(driver, work_location)
    if external_auto_submit and not submitted and _submit_form_still_open(driver):
        ok, submit_reason = _attempt_submit_with_fixes(driver, work_location, resume_path)
        if ok:
            submitted = True
            print_lg('Clicked Submit on external application form (final pass).')
        elif not stop_reason:
            stop_reason = submit_reason

    if submitted:
        return True, 'External Applied', False, stop_reason or 'Submitted successfully'

    blockers = _summarize_form_blockers(driver)
    platform = _detect_ats_platform(driver)
    platform_note = f'ATS: {platform}' if platform != 'Unknown' else ''
    if next_clicks >= external_apply_max_steps:
        reason = f'Reached max {external_apply_max_steps} Next clicks without completing form'
        if platform_note:
            reason = f'{reason}; {platform_note}'
        if blockers:
            reason = f'{reason}; {blockers}'
        print_lg(reason)
        return False, 'External tab open — finish manually', False, reason

    reason = stop_reason or 'External application not submitted'
    if platform_note:
        reason = f'{reason}; {platform_note}'
    if blockers:
        reason = f'{reason}; {blockers}'
    if last_error and last_error not in reason:
        reason = f'{reason}; {last_error}'
    print_lg(f'External apply incomplete — {reason}')
    return False, 'External tab open — finish and submit manually', False, reason
