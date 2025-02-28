# Trinity College Language Assessment App

Welcome to the **Trinity College Language Assessment App**, a web-based platform designed to help candidates prepare for the ISE Digital Speaking, Writing, Reading, and Listening assessments. The app provides dynamic feedback for speaking and writing tasks using **OpenAI GPT-4** and **Whisper API** to process speech.

## 🚀 Features

- **Speaking Tasks:** Record responses to questions, transcribe them with OpenAI Whisper, and get detailed feedback on task fulfillment, language, and delivery.
- **Writing Tasks:** Submit responses to various writing prompts and receive structured feedback.
- **Dynamic Feedback:** AI-generated feedback is displayed dynamically with suggestions on what candidates did well and where they could improve.
- **Multiple Questions:** Navigate through sequential speaking tasks.

## 🛠️ Technologies Used

- **Flask:** Backend web framework for handling routes and logic.
- **JavaScript:** Client-side interaction and audio recording logic.
- **OpenAI Whisper:** For transcribing speech responses.
- **OpenAI GPT-4:** For generating feedback.
- **Bootstrap:** For clean and responsive UI.
- **Heroku:** For deployment.
- **python-dotenv:** To manage environment variables securely.

## 🔑 Requirements

Ensure you have the following installed:

- **Python 3.8 or higher**
- **pip**
- **virtualenv**

## 📦 Setup and Installation

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/your-repo-name.git
    cd your-repo-name
    ```

2. **Create and Activate a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate
    ```

3. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set Environment Variables:**
    Create a `.env` file in the project root and add:
    ```plaintext
    FLASK_SECRET_KEY=your_secret_key
    OPENAI_API_KEY=your_openai_api_key
    ```

5. **Run the Application Locally:**
    ```bash
    flask run
    ```
    The app will be available at `http://127.0.0.1:5000`

## 📤 Deploying to Heroku

1. **Login to Heroku:**
    ```bash
    heroku login
    ```

2. **Set Heroku Remote:**
    ```bash
    heroku git:remote -a your-heroku-app-name
    ```

3. **Commit and Push:**
    ```bash
    git add .
    git commit -m "Ready for deployment"
    git push heroku main
    ```

4. **Set Environment Variables on Heroku:**
    ```bash
    heroku config:set FLASK_SECRET_KEY=your_secret_key
    heroku config:set OPENAI_API_KEY=your_openai_api_key
    ```

5. **Open the App:**
    ```bash
    heroku open
    ```

## 📂 Project Structure
```
.
├── app
│   ├── templates
│   │   ├── speaking_task_1.html          # Speaking task input page
│   │   ├── speaking_task_1_feedback.html # Dynamic feedback page
│   │   └── layout.html                   # Base layout template
│   ├── static
│   │   ├── css
│   │   └── js
│   │       └── speaking_task_1.js        # JavaScript for handling recordings
│   └── routes.py                         # Main routes and logic
├── .env                                  # Environment variables
├── requirements.txt                      # Dependencies
└── README.md                             # Project documentation
```

## 🔊 Speaking Task Flow

1. Navigate to the speaking task page (`/speaking_task_1_q1`).
2. Click **Start Recording** to record your response.
3. Click **Submit and Get Feedback** before or after the timer reaches 0.
4. Receive feedback dynamically:
    - General Comment
    - What You Did Well
    - What You Could Improve

## 🔍 Writing Task Flow

1. Navigate to the writing task page.
2. Enter your response and submit.
3. Receive structured feedback based on task fulfillment, grammar, and coherence.

## 🤖 AI Integration
- **OpenAI Whisper** processes and transcribes audio.
- **GPT-4** generates feedback based on the transcribed or written response.

## 🔧 Troubleshooting

1. **App not running locally:**
    - Check if your virtual environment is activated.
    - Ensure all dependencies are installed using `pip install -r requirements.txt`.

2. **Deployment issues on Heroku:**
    - Check the logs using:
      ```bash
      heroku logs --tail
      ```
    - Ensure environment variables are correctly set using:
      ```bash
      heroku config
      ```

3. **Feedback not displaying:**
    - Ensure your OpenAI API key is correct.
    - Check the server logs for any issues during the feedback generation.

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 🛡️ License
This project is licensed under the MIT License.

## 📞 Contact
If you have any questions, please feel free to contact:
- Gavin Reid
- gavinjohnreid@gmail.com
- [Your GitHub](https://github.com/GavinReid82)

# Updated for deployment
# Updated for deployment
# Updated for deployment
