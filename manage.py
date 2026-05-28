from app import create_app

app = create_app()

if __name__ == '__main__':
    # Local loopback address config optimized to eliminate external Android security blocks
    app.run(host='127.0.0.1', port=5500, debug=True)

