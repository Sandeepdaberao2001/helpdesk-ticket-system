from backend.app import app


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], port=5000)
