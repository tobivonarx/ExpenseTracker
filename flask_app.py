from app import create_app

# Create the Flask application instance using the create_app function from the app module.
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)