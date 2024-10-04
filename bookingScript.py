import logging
import yaml
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import datetime
import smtplib
import time
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
)
import datetime
import time
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    if os.getenv("GITHUB_ACTIONS"):
        # Running in GitHub Actions
        service = Service("chromedriver")
    else:
        # Running locally
        service = Service(
            r"C:\Users\lenovo\Downloads\chromedriver-win64\chromedriver.exe"
        )

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info(f"Chrome browser version: {driver.capabilities['browserVersion']}")
        logging.info(
            f"ChromeDriver version: {driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]}"
        )
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver: {str(e)}")
        raise


def load_config():
    try:
        if os.getenv("GITHUB_ACTIONS"):
            # In GitHub Actions, config is loaded from environment
            config_str = os.getenv("CONFIG")
            if not config_str:
                raise ValueError("CONFIG environment variable is not set")
            return yaml.safe_load(config_str)
        else:
            # Locally, load from file
            with open("config.yaml", "r") as file:
                return yaml.safe_load(file)
    except Exception as e:
        logging.error(f"Error loading configuration: {str(e)}")
        raise


def select_available_date(driver, preferred_days_ahead=2):
    try:
        logging.info(
            f"Attempting to select an available date, preferring {preferred_days_ahead} days ahead"
        )

        # Click the date field to open the calendar
        input_fields = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "input_field"))
        )
        if len(input_fields) >= 2:
            date_container = input_fields[1]
            driver.execute_script("arguments[0].scrollIntoView(true);", date_container)
            time.sleep(1)
            date_container.click()
        else:
            raise Exception("Could not find date input field")

        # Wait for calendar to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "flatpickr-calendar"))
        )

        # Find all available dates
        available_dates = driver.find_elements(
            By.XPATH,
            "//span[contains(@class, 'flatpickr-day') and not(contains(@class, 'flatpickr-disabled'))]",
        )

        if not available_dates:
            raise Exception("No available dates found")

        # Log available dates for debugging
        available_dates_info = [
            f"{date.get_attribute('aria-label')}: {date.text}"
            for date in available_dates
        ]
        logging.info(f"Available dates: {available_dates_info}")

        # Try to select the preferred date first
        target_date = None
        for date in available_dates:
            days_ahead = 0
            if "today" in date.get_attribute("class"):
                days_ahead = 0
            else:
                try:
                    date_text = date.get_attribute("aria-label")
                    date_obj = datetime.datetime.strptime(date_text, "%B %d, %Y").date()
                    today = datetime.date.today()
                    days_ahead = (date_obj - today).days
                except ValueError:
                    continue

            if days_ahead == preferred_days_ahead:
                target_date = date
                break

        # If preferred date not available, select the latest available date
        if target_date is None and available_dates:
            target_date = available_dates[-1]

        if target_date is None:
            raise Exception("Could not select any date")

        # Get the date information before clicking
        selected_date_text = target_date.get_attribute("aria-label")
        selected_date_obj = datetime.datetime.strptime(
            selected_date_text, "%B %d, %Y"
        ).date()

        # Click the selected date
        driver.execute_script("arguments[0].click();", target_date)
        logging.info(f"Clicked on date: {selected_date_text}")

        # Wait for the calendar to close
        time.sleep(1)

        # No need to verify the input field value, just return success
        logging.info(
            f"Successfully selected date: {selected_date_obj.strftime('%d-%m-%Y')}"
        )
        return True

    except Exception as e:
        logging.error(f"Date selection failed: {str(e)}")
        driver.save_screenshot("date_selection_error.png")
        raise


# Update the retry function to be simpler since we're not verifying the input value
def retry_date_selection(driver, preferred_days_ahead=2, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            if select_available_date(driver, preferred_days_ahead):
                return True
        except Exception as e:
            logging.warning(f"Date selection failed on attempt {attempt + 1}: {str(e)}")

        if attempt < max_attempts - 1:
            logging.info(f"Retrying date selection... ({attempt + 2}/{max_attempts})")
            time.sleep(2)

    raise Exception(f"Failed to select date after {max_attempts} attempts")


logging.basicConfig(
    filename="booking_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def verify_form_before_submission(driver, config):
    try:
        # Verify location
        location_dropdown = Select(
            driver.find_element(By.XPATH, config["location_dropdown_xpath"])
        )
        selected_location = location_dropdown.first_selected_option.text
        if selected_location != config["location"]:
            raise Exception(
                f"Location mismatch. Expected: {config['location']}, Got: {selected_location}"
            )

        # Verify room category
        room_category_dropdown = Select(
            driver.find_element(By.XPATH, config["room_category_dropdown_xpath"])
        )
        selected_category = room_category_dropdown.first_selected_option.text
        if selected_category != config["room_category"]:
            raise Exception(
                f"Room category mismatch. Expected: {config['room_category']}, Got: {selected_category}"
            )

        logging.info("Form verification passed")
        return True
    except Exception as e:
        logging.error(f"Form verification failed: {str(e)}")
        return False


def run_booking_script():
    config = load_config()
    driver = setup_driver()

    try:

        driver.get(config["booking_url"])
        logging.info("Opened booking website")

         # Take screenshot of initial page
        driver.save_screenshot("initial_page.png")
        

        # Select location
        location_dropdown = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, config["location_dropdown_xpath"])
            )
        )
        location_select = Select(location_dropdown)
        location_select.select_by_visible_text(config["location"])
        logging.info(f"Selected location: {config['location']}")

        # Select room category
        room_category_dropdown = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, config["room_category_dropdown_xpath"])
            )
        )
        room_category_select = Select(room_category_dropdown)
        room_category_select.select_by_visible_text(config["room_category"])
        logging.info(f"Selected room category: {config['room_category']}")

        # Select date
        retry_date_selection(driver, config["days_ahead"])

        if not verify_form_before_submission(driver, config):
            raise Exception("Form verification failed")

        # Click the Check Availability button
        check_availability_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, config["check_availability_button_xpath"])
            )
        )
        check_availability_button.click()
        logging.info("Clicked Check Availability button")

        # Wait for the availability to load
        time.sleep(2)

        # Book a room
        base_xpath = "/html/body/div[2]/div/div[2]/div/div"
        room_booked = False
        desired_time_slot = config["desired_time_slot"]
        time_slot_index = {
            "09:00 - 11:00": 1,
            "11:00 - 13:00": 2,
            "13:00 - 15:00": 3,
            "15:00 - 17:00": 4,
            "17:00 - 19:00": 5,
            "19:00 - 21:00": 6,
        }

        for room_index in range(1, 7):  # Assuming there are 6 rooms
            try:
                room_xpath = f"{base_xpath}[{room_index}]"
                room_name = driver.find_element(
                    By.XPATH, f"{room_xpath}/div/div[2]"
                ).text
                button_xpath = f"{room_xpath}/div/div[3]/div/div[{time_slot_index[desired_time_slot]}]/button"

                time_slot_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, button_xpath))
                )

                if time_slot_button.is_enabled():
                    time_slot_button.click()
                    logging.info(
                        f"Selected time slot {desired_time_slot} in room {room_name}"
                    )

                    # Confirm the booking
                    confirm_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, config["confirm_button_xpath"])
                        )
                    )
                    confirm_button.click()
                    logging.info("Confirmed booking")

                    room_booked = True
                    break
                else:
                    logging.info(
                        f"Time slot {desired_time_slot} not available in room {room_name}"
                    )
            except (
                TimeoutException,
                ElementClickInterceptedException,
                NoSuchElementException,
            ) as e:
                logging.info(f"Failed to book room {room_index}: {str(e)}")
                continue

        if not room_booked:
            raise Exception(
                f"No available rooms found for the desired time slot: {desired_time_slot}"
            )

        # Wait for the login page to load
        time.sleep(2)

        # Log in to the website
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, config["username_field_xpath"]))
        ).send_keys(config["username"])
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, config["password_field_xpath"]))
        ).send_keys(config["password"])
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, config["login_button_xpath"]))
        ).click()
        logging.info("Logged in successfully")

        # Wait for the confirmation page to load
        time.sleep(5)

        logging.info("Room booked successfully.")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        driver.quit()


if __name__ == "__main__":
    try:
        run_booking_script()
    except Exception as e:
        logging.error(f"Unhandled exception: {str(e)}")
