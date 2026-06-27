'''
Fill job application forms on external company websites (Workday, Greenhouse, etc.).
Does not auto-submit by default — leaves the tab open for manual review and submit.
'''

import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)

from config.personals import *
from config.questions import *
from config.search import external_apply_max_steps, fill_external_application_forms, external_auto_submit
from config.settings import click_gap
from modules.helpers import buffer, print_lg


NEXT_BUTTON_XPATHS = [
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'save and continue')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
    ".//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
]

SUBMIT_BUTTON_XPATHS = [
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit application')]",
    ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
    ".//input[@type='submit']",
]


def _field_context(element) -> str:
    parts = []
    for attr in ('aria-label', 'placeholder', 'name', 'id', 'autocomplete'):
        value = (element.get_attribute(attr) or '').strip()
        if value:
            parts.append(value)
    try:
        eid = element.get_attribute('id')
        if eid:
            for label in element.parent.find_elements(By.XPATH, f".//label[@for='{eid}']"):
                if label.text.strip():
                    parts.append(label.text.strip())
    except Exception:
        pass
    try:
        parent = element.find_element(By.XPATH, "./ancestor::label[1]")
        if parent.text.strip():
            parts.append(parent.text.strip())
    except Exception:
        pass
    return ' '.join(parts).lower()


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
    if 'citizenship' in context or 'authorized' in context or 'eligible to work' in context:
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
            if not any(word in context for word in ('email', 'phone', 'name', 'resume', 'cv', 'required')):
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
    if selected and selected not in ('', 'select', 'select an option', 'choose', 'please select'):
        return
    answer = _answer_for_context(context, work_location)
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
            if candidate.lower() in option.lower() or option.lower() in candidate.lower():
                select.select_by_visible_text(option)
                return


def _upload_resume_if_needed(driver: WebDriver, resume_path: str) -> bool:
    if not resume_path or not os.path.isfile(resume_path):
        return False
    uploaded = False
    for inp in driver.find_elements(By.CSS_SELECTOR, "input[type='file']"):
        try:
            if not inp.is_displayed():
                continue
            context = _field_context(inp)
            if uploaded and 'resume' not in context and 'cv' not in context:
                continue
            inp.send_keys(os.path.abspath(resume_path))
            uploaded = True
            print_lg(f'Uploaded resume on external form: {os.path.basename(resume_path)}')
            buffer(click_gap)
        except Exception:
            continue
    return uploaded


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
    return filled


def _click_button(driver: WebDriver, xpaths: list[str]) -> bool:
    for xpath in xpaths:
        for btn in driver.find_elements(By.XPATH, xpath):
            try:
                if not btn.is_displayed() or not btn.is_enabled():
                    continue
                text = (btn.text or btn.get_attribute('value') or '').lower()
                if 'cookie' in text or 'accept all' in text:
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


def fill_and_submit_external_form(
    driver: WebDriver,
    work_location: str,
    job_description: str | None,
    resume_path: str,
    actions,
) -> tuple[bool, str]:
    '''
    Fills external application fields. Does not click Next/Submit if required fields are still empty.
    By default does not click Submit — tab stays open for manual submit.
    '''
    if not fill_external_application_forms:
        return False, 'External form fill disabled'

    print_lg('Filling external application form (tab will stay open for you to submit)...')
    submitted = False

    for step in range(external_apply_max_steps):
        try:
            _upload_resume_if_needed(driver, resume_path)
            filled = _fill_page_fields(driver, work_location)
            if filled:
                print_lg(f'Filled {filled} field(s) on external form (step {step + 1}).')

            unanswered = _count_unanswered_required(driver)
            if unanswered > 0:
                print_lg(f'Stopping — {unanswered} required field(s) still empty. Tab left open for you to complete and submit.')
                break

            if external_auto_submit and _click_button(driver, SUBMIT_BUTTON_XPATHS):
                submitted = True
                print_lg('Clicked Submit on external application form.')
                buffer(2)
                break

            if _click_button(driver, NEXT_BUTTON_XPATHS):
                print_lg(f'Clicked Next/Continue on external form (step {step + 1}).')
                buffer(2)
                continue

            if step == 0:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                buffer(2)
                continue
            break
        except Exception as e:
            print_lg(f'External form step {step + 1} error: {e}')
            break

    if submitted:
        return True, 'External Applied'
    return False, 'External tab open — finish and submit manually'
