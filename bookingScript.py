from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import time
import datetime

# Initialize the WebDriver using webdriver-manager with Service
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Open the booking website
driver.get("https://spaces.xmu.edu.my/")

# Wait for the page to load
time.sleep(5)

# Wait for the location dropdown to be present
location_dropdown = WebDriverWait(driver, 20).until(
    EC.presence_of_element_located(
        (By.XPATH, "/html/body/div[2]/div[2]/form/div/div[1]/div/select")
    )
)
location_select = Select(location_dropdown)
location_select.select_by_visible_text("A3 Main Library")

# Wait for the room category dropdown to be present
room_category_dropdown = WebDriverWait(driver, 20).until(
    EC.presence_of_element_located(
        (By.XPATH, "/html/body/div[2]/div[2]/form/div/div[2]/div[2]/div/div/select")
    )
)
room_category_select = Select(room_category_dropdown)
room_category_select.select_by_visible_text("Group Discussion Room")

# Interact with the date picker
booking_date_field = WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.ID, "booking_date"))
)
booking_date_field.click()

# Get the date two days from now
target_date = datetime.date.today() + datetime.timedelta(days=3)
booking_date = target_date.strftime("%Y-%m-%d")
print(f"Booking date: {booking_date}")

# Select the correct date in the date picker
month_year = target_date.strftime("%B %Y")
day = str(target_date.day)
print(f"{day}")

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
except:
    print(f"Failed to click on day {day}. Trying JavaScript click.")
    driver.execute_script("arguments[0].click();", day_element)

time.sleep(1)

# Click the Check Availability button
check_availability_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (By.XPATH, "/html/body/div[2]/div[2]/form/div/div[3]/div/div[2]/button")
    )
)
check_availability_button.click()

# Wait for the availability to load
time.sleep(5)

# Select the desired time slot, e.g., 15:00 - 17:00
desired_time_slot = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            "/html/body/div[2]/div/div[2]/div/div[3]/div/div[3]/div/div[4]/button",
        )
    )
)
desired_time_slot.click()

# Confirm the booking
confirm_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/div[6]/button[1]"))
)
confirm_button.click()

# Wait for the login page to load
time.sleep(5)

# Log in to the website
username = "username"  # Replace with your username
password = "password"  # Replace with your password

# Assuming there are fields with id 'username' and 'password' and a login button
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located(
        (By.XPATH, "/html/body/div[2]/div/form/div/div[1]/div/input")
    )
).send_keys(username)
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located(
        (By.XPATH, "/html/body/div[2]/div/form/div/div[2]/div/input")
    )
).send_keys(password)
WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (By.XPATH, "/html/body/div[2]/div/form/div/div[3]/div/div/button")
    )
).click()

# Wait for the confirmation page to load
time.sleep(5)

# Print success message
print("Room booked successfully.")

# Close the browser
driver.quit()
