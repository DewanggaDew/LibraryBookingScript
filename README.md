# LibraryBookingScript

This script is used for automated booking within the XMUM Library, to allow students to book rooms automatically.

## Before Cloning

Download a Chromedriver that supports your current Chrome browser

Download from: https://googlechromelabs.github.io/chrome-for-testing/

Tutorial Video: https://www.youtube.com/watch?v=KqWUC-xWYpA

## Run Locally

Clone the project

```bash
  git clone https://github.com/DewanggaDew/LibraryBookingScript
```

Go to the project directory

```bash
  cd LibraryBookingScript
```

Install dependencies

```bash
  pip install -r requirements.txt
```

Edit the config.yaml file to your liking (Change the XPATH if only you need to)

```bash
#true for the web browser to not open, false to make the browser open
headless: true

location: "A3 Main Library"

#Change the room category
room_category: "Silent Study Room"

#Recommended to have 2 days ahead and run the script everyday, to book the script everyday
days_ahead: 2

#Change desired booking time
desired_time_slot: "15:00 - 17:00"

#Change to your own username
username: "username"

#Change to your own password
password: "password"

```

## Contributing

Contributions are always welcome!

Please fork this project with my permission

Please adhere to this project's `code of conduct`.

## Authors

- [@DewanggaDew](https://github.com/DewanggaDew)
