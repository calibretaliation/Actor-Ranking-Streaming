import json

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from .objects import Experience, Education, Scraper, Skill, Interest, Accomplishment, Contact
import os
import re
from linkedin_scraper import selectors
import posixpath


class Person(Scraper):
    __TOP_CARD = "pv-top-card"
    __WAIT_FOR_ELEMENT_TIMEOUT = 5

    def __init__(
            self,
            linkedin_url=None,
            name=None,
            about=None,
            experiences=None,
            educations=None,
            interests=None,
            accomplishments=None,
            company=None,
            job_title=None,
            contacts=None,
            skills=None,
            driver=None,
            get=True,
            scrape=True,
            close_on_complete=True,
    ):
        self.linkedin_url = linkedin_url
        self.data = {
            'name': name,
            'linkedin_url': linkedin_url,
            'about': about or [],
            'experiences': experiences or [],
            'educations': educations or [],
            'interests': interests or [],
            'accomplishments': accomplishments or [],
            'also_viewed_urls': [],
            'contacts': contacts or [],
            'skills': skills or [],
        }

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") == None:
                    driver_path = os.path.join(
                        os.path.dirname(__file__), "drivers/chromedriver"
                    )
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        if get:
            driver.get(linkedin_url)

        self.driver = driver

        if scrape:
            self.scrape(close_on_complete)

    def add_name(self, name):
        self.data['name'] = name

    def add_about(self, about):
        self.data['about'].append(about)

    def add_experience(self, experience):
        self.data['experiences'].append(experience)

    def add_education(self, education):
        self.data['educations'].append(education)

    def add_interest(self, interest):
        self.data['interests'].append(interest)

    def add_accomplishment(self, accomplishment):
        self.data['accomplishments'].append(accomplishment)

    def add_location(self, location):
        self.data['location'] = location

    def add_contact(self, contact):
        self.data['contacts'].append(contact)

    def add_skill(self, skill):
        self.data['skills'].append(skill)

    def scrape(self, close_on_complete=True):
        if self.is_signed_in():
            self.scrape_logged_in(close_on_complete=close_on_complete)
        else:
            print("you are not logged in!")
            x = input(
                "please verify the capcha then press any key to continue...")
            self.scrape_not_logged_in(close_on_complete=close_on_complete)

    def _click_see_more_by_class_name(self, class_name):
        try:
            _ = WebDriverWait(self.driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, class_name))
            )
            div = self.driver.find_element(By.CLASS_NAME, class_name)
            div.find_element(By.TAG_NAME, "button").click()
        except Exception as e:
            pass

    def scrape_logged_in(self, close_on_complete=True):
        driver = self.driver
        duration = None

        root = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.CLASS_NAME,
                    self.__TOP_CARD,
                )
            )
        )

        self.add_name(root.find_element(
            By.CLASS_NAME, selectors.NAME).text.strip())

        # get about
        try:
            about = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        # "//*[@class='lt-line-clamp__raw-line']",
                        "//*[@id='about']//following-sibling::div[2]//descendant::span",
                    )
                )
            )
        except:
            about = None
        if about:
            self.add_about(about.text.strip())

        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));"
        )

        # get experience
        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight*3/5));"
        )

        driver.get(posixpath.join(self.linkedin_url, 'details', 'experience'))
        _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[contains(@id,'profilePagedListComponent')]"
                )
            )
        )

        for position in driver.find_elements(By.XPATH, "//*[contains(@id,'profilePagedListComponent') and not(contains(@id,'EXPERIENCE-VIEW-DETAILS-profilePositionGroup'))]"):
            sub_positions = position.find_elements(
                By.XPATH, ".//*[contains(@id,'profilePagedListComponent') and contains(@id,'EXPERIENCE-VIEW-DETAILS-profilePositionGroup')]")
            if len(sub_positions) > 0:
                head = position.find_element(
                    By.XPATH, ".//a[contains(@class, 'flex-column')]")
                company_name = head.find_element(
                    By.XPATH, ".//*[contains(@class, 't-bold')]//child::span").text.strip()
                company_link = head.get_attribute('href')
                try:
                    location = head.find_element(
                        By.XPATH, ".//*[contains(@class, 't-black--light')]//child::span").text.strip()
                except:
                    location = None

                for subPos in sub_positions:
                    head = subPos.find_element(By.XPATH, './/a')
                    position_title = head.find_element(
                        By.XPATH, ".//*[contains(@class, 't-bold')]//child::span").text.strip()
                    try:
                        times = head.find_element(
                            By.XPATH, ".//*[contains(@class, 't-normal') and not(contains(@class, 't-black--light'))]//child::span").text.strip()
                    except:
                        times = None

                    try:
                        side_details = head.find_elements(
                            By.XPATH, ".//span[contains(@class, 't-black--light')]//child::span")
                        date, duration = [t.strip()
                                          for t in side_details[0].text.strip().split('·')]
                        from_date, to_date = [t.strip()
                                              for t in date.split('-')]
                    except:
                        from_date = None
                        to_date = None
                        duration = None

                    try:
                        description = subPos.find_element(
                            By.XPATH, ".//*[@class='pvs-list__outer-container']").text.strip()
                    except:
                        description = None

                    experience = Experience(
                        position_title=position_title,
                        from_date=from_date,
                        to_date=to_date,
                        duration=duration,
                        location=location,
                        times=times,
                        description=description,
                        website=company_link,
                        institution_name=company_name,
                    )
                    self.add_experience(experience)
                continue

            try:
                position_title = position.find_element(
                    By.XPATH, ".//*[contains(@class, 't-bold')]//child::span").text.strip()
            except:
                continue

            details = position.find_elements(
                By.XPATH, ".//*[contains(@class, 't-normal')]//child::span")

            side_details = position.find_elements(
                By.XPATH, ".//span[contains(@class, 't-black--light')]//child::span")

            try:
                l = details[0].text.strip()
                i = l.index('·')
                company_name, times = l[:i].strip(), l[i+1:].strip()
            except:
                company_name = details[0].text.strip()
                times = None

            try:
                date, duration = [t.strip()
                                  for t in side_details[0].text.strip().split('·')]
                from_date, to_date = [t.strip() for t in date.split('-')]
            except:
                from_date = None
                to_date = None
                duration = None

            try:
                location = side_details[2].text.strip()
            except:
                location = None

            try:
                company_link = position.find_element(
                    By.XPATH, './/a').get_attribute('href')
            except:
                company_link = None

            try:
                description = position.find_element(
                    By.XPATH, ".//*[@class='pvs-list__outer-container']").text.strip()
            except:
                description = None

            experience = Experience(
                position_title=position_title,
                from_date=from_date,
                to_date=to_date,
                duration=duration,
                location=location,
                times=times,
                description=description,
                website=company_link,
                institution_name=company_name,
            )
            self.add_experience(experience)
        # # get location
        # location = driver.find_element(By.CLASS_NAME, f"{self.__TOP_CARD}--list-bullet")
        # location = location.find_element(By.TAG_NAME, "li").text
        # self.add_location(location)

        # driver.execute_script(
        #     "window.scrollTo(0, Math.ceil(document.body.scrollHeight/1.5));"
        # )

        # get education
        driver.get(posixpath.join(self.linkedin_url, 'details', 'education'))
        _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[contains(@id,'profilePagedListComponent')]"
                )
            )
        )
        for school in driver.find_elements(By.XPATH, "//*[contains(@id,'profilePagedListComponent')]"):
            try:
                school_name = school.find_element(
                    By.XPATH, ".//*[contains(@class, 't-bold')]//child::span").text.strip()
            except:
                continue
            try:
                website = school.find_element(
                    By.XPATH, ".//a").get_attribute('href')
            except:
                website = None

            try:
                l = school.find_element(
                    By.XPATH, ".//a[contains(@class, 'flex-column')]//child::span[contains(@class,'t-normal') and not(contains(@class, 't-black--light'))]//child::span").text.strip()
                i = l.index(',')
                degree, field_of_study = l[:i].strip(), l[i+1:].strip()
            except NoSuchElementException:
                degree, field_of_study = None, None
            except ValueError:
                degree = school.find_element(
                    By.XPATH, ".//a[contains(@class, 'flex-column')]//child::span[contains(@class,'t-normal') and not(contains(@class, 't-black--light'))]//child::span").text.strip()
                field_of_study = None

            try:
                l = school.find_element(
                    By.XPATH, ".//a[contains(@class, 'flex-column')]//child::span[contains(@class,'t-black--light')]//child::span").text.strip()
                i = l.index('-')
                from_date, to_date = l[:i].strip(), l[i+1:].strip()
            except NoSuchElementException:
                from_date, to_date = None, None
            except ValueError:
                from_date = school.find_element(
                    By.XPATH, ".//a[contains(@class, 'flex-column')]//child::span[contains(@class,'t-black--light')]//child::span").text.strip()
                to_date = None

            grade, activities, description = None, None, None
            for li in school.find_elements(By.XPATH, ".//div[@class='pvs-list__outer-container']//child::ul//child::li[@class=' ']"):
                try:
                    text = li.find_element(By.XPATH, ".//span").text.strip()
                except:
                    continue
                if text.startswith('Grade'):
                    m = re.search(r'Grade: ([\s\S]+)', text)
                    grade = m.group(1).strip()
                elif text.startswith('Activities and societies'):
                    m = re.search(r'Activities and societies: ([\s\S]+)', text)
                    activities = m.group(1).strip()
                else:
                    description = text

            education = Education(
                from_date=from_date,
                to_date=to_date,
                degree=degree,
                description=description,
                institution_name=school_name,
                field_of_study=field_of_study,
                grade=grade,
                activities=activities,
                website=website,
            )
            self.add_education(education)

        # driver.get(self.linkedin_url)

        driver.get(posixpath.join(self.linkedin_url, 'details', 'skills'))
        try:
            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[contains(@id,'profilePagedListComponent')]"
                    )
                )
            )
        except:
            pass
        for tag in driver.find_elements(By.XPATH, ".//*[@class = 'pvs-tab__pill-choices']//child::button"):
            TAG = tag.text.strip().upper().replace(' ', '-')
            if TAG == 'ALL':
                continue
            for skill_ele in driver.find_elements(By.XPATH, f".//li[contains(@id,'{TAG[:5]}')]"):
                skill_name = skill_ele.find_element(
                    By.XPATH, ".//span[contains(@class, 't-bold')]//child::span[@class='visually-hidden']").get_attribute('innerHTML')
                name = re.search(r'>([\s\S]+)<', skill_name).group(1).strip()
                skill = Skill(
                    name=name,
                    tag=TAG,
                )
                self.add_skill(skill)

        # driver.get(posixpath.join(self.linkedin_url, 'details', 'featured'))
        # driver.get(posixpath.join(self.linkedin_url, 'details', 'honors'))
        # driver.get(posixpath.join(self.linkedin_url, 'details', 'publications'))
        # driver.get(posixpath.join(self.linkedin_url, 'details', 'interests'))
        # driver.get(posixpath.join(self.linkedin_url, 'details', 'projects'))
        # get interest
        # try:

        #     _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
        #         EC.presence_of_element_located(
        #             (
        #                 By.XPATH,
        #                 "//*[@class='pv-profile-section pv-interests-section artdeco-container-card artdeco-card ember-view']",
        #             )
        #         )
        #     )
        #     interestContainer = driver.find_element(By.XPATH,
        #                                             "//*[@class='pv-profile-section pv-interests-section artdeco-container-card artdeco-card ember-view']"
        #                                             )
        #     for interestElement in interestContainer.find_elements(By.XPATH,
        #                                                            "//*[@class='pv-interest-entity pv-profile-section__card-item ember-view']"
        #                                                            ):
        #         interest = Interest(
        #             interestElement.find_element(
        #                 By.TAG_NAME, "h3").text.strip()
        #         )
        #         self.add_interest(interest)
        # except:
        #     pass

        # get accomplishment
        # try:
        #     _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
        #         EC.presence_of_element_located(
        #             (
        #                 By.XPATH,
        #                 "//*[@class='pv-profile-section pv-accomplishments-section artdeco-container-card artdeco-card ember-view']",
        #             )
        #         )
        #     )
        #     acc = driver.find_element(By.XPATH,
        #                               "//*[@class='pv-profile-section pv-accomplishments-section artdeco-container-card artdeco-card ember-view']"
        #                               )
        #     for block in acc.find_elements(By.XPATH,
        #                                    "//div[@class='pv-accomplishments-block__content break-words']"
        #                                    ):
        #         category = block.find_element(By.TAG_NAME, "h3")
        #         for title in block.find_element(By.TAG_NAME,
        #                                         "ul"
        #                                         ).find_elements(By.TAG_NAME, "li"):
        #             accomplishment = Accomplishment(category.text, title.text)
        #             self.add_accomplishment(accomplishment)
        # except:
        #     pass

        # get connections
        # try:
        #     driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
        #     _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
        #         EC.presence_of_element_located((By.CLASS_NAME, "mn-connections"))
        #     )
        #     connections = driver.find_element(By.CLASS_NAME, "mn-connections")
        #     if connections is not None:
        #         for conn in connections.find_elements(By.CLASS_NAME, "mn-connection-card"):
        #             anchor = conn.find_element(By.CLASS_NAME, "mn-connection-card__link")
        #             url = anchor.get_attribute("href")
        #             name = conn.find_element(By.CLASS_NAME, "mn-connection-card__details").find_element(By.CLASS_NAME,
        #                                                                                                 "mn-connection-card__name").text.strip()
        #             occupation = conn.find_element(By.CLASS_NAME, "mn-connection-card__details").find_element(
        #                 By.CLASS_NAME, "mn-connection-card__occupation").text.strip()
        #
        #             contact = Contact(name=name, occupation=occupation, url=url)
        #             self.add_contact(contact)
        # except:
        #     connections = None

        if close_on_complete:
            driver.quit()

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.data.__dict__,
                          sort_keys=True, indent=4)

    @property
    def company(self):
        if self.data['experiences']:
            return (
                self.data['experiences'][0].institution_name
                if self.data['experiences'][0].institution_name
                else None
            )
        else:
            return None

    @property
    def job_title(self):
        if self.data['experiences']:
            return (
                self.data['experiences'][0].position_title
                if self.data['experiences'][0].position_title
                else None
            )
        else:
            return None

    def __repr__(self):
        return "{name}\n\nAbout\n{about}\n\nExperience\n{exp}\n\nEducation\n{edu}\n\nInterest\n{int}\n\nAccomplishments\n{acc}\n\nContacts\n{conn}".format(
            name=self.data['name'],
            about=self.data['about'],
            exp=self.data['experiences'],
            edu=self.data['educations'],
            int=self.data['interests'],
            acc=self.data['accomplishments'],
            conn=self.data['contacts'],
        )
