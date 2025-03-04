@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Downloading NLTK resources...
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

echo Setup complete. You can now run the application using:
echo python app.py --host <proxmox-host> --user <username> --password <password>
pause