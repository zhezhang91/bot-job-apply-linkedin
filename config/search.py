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


###################################################### LINKEDIN SEARCH PREFERENCES ######################################################

# These Sentences are Searched in LinkedIn
# Enter your search terms inside '[ ]' with quotes ' "searching title" ' for each search followed by comma ', ' Eg: ["Software Engineer", "Software Developer", "Selenium Developer"]
search_terms = [
    "Software Engineer",
    "Software Developer",
    "Web Developer",
    "Full Stack Developer",
    "Fullstack Developer",
    "Frontend Developer",
    "Front End Developer",
    "Backend Developer",
    "Back End Developer",
    "Application Developer",
    "JavaScript Developer",
    "React Developer",
    "Node.js Developer",
    "Python Developer",
    "Java Developer",
]

# Job title must contain at least one of these phrases (case-insensitive). Leave empty [] to disable.
allowed_job_title_keywords = []    # Disabled — rely on search_terms instead (broader matching)

# Skip jobs whose title contains any of these phrases (case-insensitive).
blocked_job_title_keywords = [
    "intern", "internship", "co-op", "co op",
    "recruiter", "talent acquisition",
]

# Skip companies whose name contains these words (case-insensitive). Helps filter staffing agencies.
blocked_company_name_keywords = [
    "staffing agency", "employment agency", "headhunt", "manpower",
]

# Only apply to companies with at least this many employees. Set to 0 to disable.
min_company_size = 0

# Skip companies larger than this many employees. Set to 0 for no upper limit.
max_company_size = 0

# If True, skip jobs when company size cannot be detected on LinkedIn.
skip_unknown_company_size = False

# Search location, this will be filled in "City, state, or zip code" search box. If left empty as "", tool will not fill it.
search_location = ""               # Some valid examples: "", "United States", "India", "Chicago, Illinois, United States", "90001, Los Angeles, California, United States", "Bengaluru, Karnataka, India", etc.

# After how many number of applications in current search should the bot switch to next search? 
switch_number = 30                 # Only numbers greater than 0... Don't put in quotes

# Set False to skip Saved jobs and go straight to keyword search + apply.
apply_saved_jobs_first = False     # True or False, Note: True or False are case-sensitive
search_new_jobs_after_saved = True # Run keyword searches with your filters.
saved_jobs_url = "https://www.linkedin.com/jobs/collections/saved/"   # LinkedIn Saved jobs (Jobs > My jobs > Saved)
saved_jobs_limit = 0               # Max saved jobs to apply per run. 0 = apply to all saved jobs.
relax_filters_for_saved_jobs = True  # True = skip title/location/company-size/date filters for jobs you saved manually

# Do you want to randomize the search order for search_terms?
randomize_search_order = False     # True of False, Note: True or False are case-sensitive


# >>>>>>>>>>> Job Search Filters <<<<<<<<<<<
''' 
You could set your preferences or leave them as empty to not select options except for 'True or False' options. Below are some valid examples for leaving them empty:
This is below format: QUESTION = VALID_ANSWER

## Examples of how to leave them empty. Note that True or False options cannot be left empty! 
* question_1 = ""                    # answer1, answer2, answer3, etc.
* question_2 = []                    # (multiple select)
* question_3 = []                    # (dynamic multiple select)

## Some valid examples of how to answer questions:
* question_1 = "answer1"                  # "answer1", "answer2", "answer3" or ("" to not select). Answers are case sensitive.
* question_2 = ["answer1", "answer2"]     # (multiple select) "answer1", "answer2", "answer3" or ([] to not select). Note that answers must be in [] and are case sensitive.
* question_3 = ["answer1", "Random AnswER"]     # (dynamic multiple select) "answer1", "answer2", "answer3" or ([] to not select). Note that answers must be in [] and need not match the available options.

'''

sort_by = "Most recent"                       # "Most recent", "Most relevant" or ("" to not select) 
date_posted = "Past month"         # LinkedIn filter: "Any time", "Past month", "Past week", "Past 24 hours" or ("" to not select)

# Skip jobs posted more than this many days ago. Set to 0 to disable.
max_days_since_posted = 0
salary = ""                        # "$40,000+", "$60,000+", "$80,000+", "$100,000+", "$120,000+", "$140,000+", "$160,000+", "$180,000+", "$200,000+"

# LinkedIn search filter: True = only show Easy Apply jobs in search results.
easy_apply_only = False            # False = also include jobs that apply on company websites

# External apply: fill company-site forms; leave the tab open for you to submit manually.
apply_external_jobs = True         # True or False, Note: True or False are case-sensitive
fill_external_application_forms = True   # Auto-fill fields on external sites
external_auto_submit = False       # False = never click Submit; you finish and submit in the open tab
keep_external_apply_tabs_open = True     # Always leave external apply tabs open (recommended)
external_apply_max_steps = 20      # Max Next/Continue clicks per external application (Submit excluded when external_auto_submit = False)

experience_level = ["Entry level", "Associate", "Mid-Senior level"]
job_type = ["Full-time"]                      # (multiple select) "Full-time", "Part-time", "Contract", "Temporary", "Volunteer", "Internship", "Other"
on_site = ["Remote", "On-site", "Hybrid"]                       # (multiple select) "On-site", "Remote", "Hybrid"

companies = []                     # (dynamic multiple select) make sure the name you type in list exactly matches with the company name you're looking for, including capitals. 
                                   # Eg: "7-eleven", "Google","X, the moonshot factory","YouTube","CapitalG","Adometry (acquired by Google)","Meta","Apple","Byte Dance","Netflix", "Snowflake","Mineral.ai","Microsoft","JP Morgan","Barclays","Visa","American Express", "Snap Inc", "JPMorgan Chase & Co.", "Tata Consultancy Services", "Recruiting from Scratch", "Epic", and so on...
location = [
    "Ottawa, Ontario, Canada",
    "Toronto, Ontario, Canada",
    "Vancouver, British Columbia, Canada",
    "Markham, Ontario, Canada",
    "Mississauga, Ontario, Canada",
]

# Skip jobs whose listed location does not contain any of these words (case-insensitive). Leave empty [] to disable.
allowed_locations = ["Canada", "Ottawa", "Toronto", "Vancouver", "Ontario", "British Columbia"]

# Nearby cities / metro areas that also count as allowed (GTA, Vancouver metro, Ottawa area).
allowed_metro_locations = [
    "Markham", "Mississauga", "Brampton", "Scarborough", "North York", "Etobicoke",
    "Richmond Hill", "Oakville", "Ajax", "Pickering", "Vaughan", "Milton", "Halton Hills",
    "Greater Toronto", "GTA", "Burnaby", "Surrey", "Richmond", "Coquitlam", "New Westminster",
    "North Vancouver", "West Vancouver", "Delta", "Langley", "Kanata", "Nepean", "Orleans",
    "Kitchener", "Waterloo", "Hamilton", "London", "Calgary", "Edmonton", "Victoria",
    "Winnipeg", "Halifax", "Gatineau", "Cambridge", "Barrie", "Guelph", "St. Catharines",
]

# Allow remote/hybrid jobs listed as "Canada" if they are not in a blocked province/city.
allow_remote_canada = True

# Skip jobs whose listed location contains any of these words (case-insensitive). Leave empty [] to disable.
blocked_locations = ["Quebec", "Québec", "Montreal", "Montréal", "Quebec City", "Québec City", "Laval", "Sherbrooke"]
industry = []                      # (dynamic multiple select)
job_function = []                  # (dynamic multiple select)
job_titles = []                    # (dynamic multiple select)
benefits = []                      # (dynamic multiple select)
commitments = []                   # (dynamic multiple select)

under_10_applicants = False        # True or False, Note: True or False are case-sensitive
in_your_network = False            # True or False, Note: True or False are case-sensitive
fair_chance_employer = False       # True or False, Note: True or False are case-sensitive


## >>>>>>>>>>> RELATED SETTING <<<<<<<<<<<

# Pause after applying filters to let you modify the search results and filters?
pause_after_filters = False         # True or False, Note: True or False are case-sensitive

##




## >>>>>>>>>>> SKIP IRRELEVANT JOBS <<<<<<<<<<<
 
# Avoid applying to these companies, and companies with these bad words in their 'About Company' section...
about_company_bad_words = ["Crossover"]       # (dynamic multiple search) or leave empty as [].

about_company_good_words = []      # (dynamic multiple search) or leave empty as [].

# Avoid applying to these companies if they have these bad words in their 'Job Description' section...
bad_words = ["US Citizen", "USA Citizen", "No C2C", "No Corp2Corp", "must be a u.s. citizen"]                     # Case Insensitive.

security_clearance = False         # True or False, Note: True or False are case-sensitive

did_masters = True                 # True or False, Note: True or False are case-sensitive

# -1 = apply regardless of years of experience listed in the job description
current_experience = -1             # Integers > -2 (Ex: -1, 0, 1, 2, 3, 4...)
##






############################################################################################################
'''
THANK YOU for using my tool 😊! Wishing you the best in your job hunt 🙌🏻!

Sharing is caring! If you found this tool helpful, please share it with your peers 🥺. Your support keeps this project alive.

Support my work on <PATREON_LINK>. Together, we can help more job seekers.

As an independent developer, I pour my heart and soul into creating tools like this, driven by the genuine desire to make a positive impact.

Your support, whether through donations big or small or simply spreading the word, means the world to me and helps keep this project alive and thriving.

Gratefully yours 🙏🏻,
Sai Vignesh Golla
'''
############################################################################################################