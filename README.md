🚀 GRC Statements — Setup & Run Guide

1. Clone the Repository
First, clone this project from GitHub:

`git clone https://github.com/<your-username>/grc0app.git`

Then move into the project folder:

`cd grc0app`

---------------------------------------------------------------------------------------------

2. Set Up Python Environment:
Make sure you have Python 3.8+ installed.
Check your version:

`python --version`

---------------------------------------------------------------------------------------------

Create a virtual environment to keep dependencies isolated:
Windows:

`python -m venv venv`
`venv\Scripts\activate`

Mac/Linux:

`python3 -m venv venv`
`source venv/bin/activate`

---------------------------------------------------------------------------------------------

3. Install Required Packages
All dependencies are listed in your requirements.txt.
Run this command inside the project folder:

`pip install -r requirements.txt`

This installs Flask and any other needed modules.

---------------------------------------------------------------------------------------------


▶5. Run the Application
Now, start your Flask app using:

`python app.py`

---------------------------------------------------------------------------------------------

If you’re on macOS/Linux, you might use:

`python3 app.py`

---------------------------------------------------------------------------------------------

You’ll see output like:
 * Running on http://127.0.0.1:5000/


---------------------------------------------------------------------------------------------


6. Open in Browser

Once running, open your web browser and go to:

http://127.0.0.1:5000/


You’ll see your Login page (GRC Statements).
From there, you can sign up, log in, and use the App/

---------------------------------------------------------------------------------------------

A default account has been pre-configured for testing purposes:
Username: `Admin` |
Password: `admin` |

---------------------------------------------------------------------------------------------