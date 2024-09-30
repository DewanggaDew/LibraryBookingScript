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


logging.basicConfig(
    filename="booking_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def load_config():
    try:
        with open("config.yaml", "r") as file:
            return yaml.safe_load(file)
    except Exception as e:
        logging.error(f"Error loading configuration: {str(e)}")
        raise


def run_booking_script():
    config = load_config()
    chrome_options = Options()
    if config["headless"]:
        chrome_options.add_argument("--headless")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        driver.get(config["booking_url"])
        logging.info("Opened booking website")

        # Wait for the location dropdown to be present
        location_dropdown = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, config["location_dropdown_xpath"])
            )
        )
        location_select = Select(location_dropdown)
        location_select.select_by_visible_text(config["location"])
        logging.info(f"Selected location: {config['location']}")

        # Wait for the room category dropdown to be present
        room_category_dropdown = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, config["room_category_dropdown_xpath"])
            )
        )
        room_category_select = Select(room_category_dropdown)
        room_category_select.select_by_visible_text(config["room_category"])
        logging.info(f"Selected room category: {config['room_category']}")

        # Interact with the date picker
        booking_date_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "booking_date"))
        )
        booking_date_field.click()

        # Get the date specified in config (e.g., 2 days from now)
        target_date = datetime.date.today() + datetime.timedelta(
            days=config["days_ahead"]
        )
        booking_date = target_date.strftime("%Y-%m-%d")
        logging.info(f"Booking date: {booking_date}")

        day = str(target_date.day)

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "/html/body/div[3]/div[2]"))
        )

        # Click on the correct day
        try:
            day_element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"/html/body/div[3]/div[2]/div/div[2]/div/span[{day}]")
                )
            )
            ActionChains(driver).move_to_element(day_element).click().perform()
        except Exception as e:
            logging.error(f"Failed to click on day {day}. Error: {str(e)}")
            driver.execute_script("arguments[0].click();", day_element)

        time.sleep(1)

        # Click the Check Availability button
        check_availability_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, config["check_availability_button_xpath"])
            )
        )
        check_availability_button.click()
        logging.info("Clicked Check Availability button")

        # Wait for the availability to load
        time.sleep(5)

        # Define the base XPath for rooms
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
                    break  # Exit the loop if a room is successfully booked
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
        time.sleep(5)

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
