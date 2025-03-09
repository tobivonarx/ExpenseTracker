from app import create_app

app = create_app()  # Keep it as 'app'

if __name__ == '__main__':
    app.run(debug=True)  # Keep this as 'app' too (for local development)