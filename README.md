# RRI Mamuju: Digital Board & Employee Portal
## Running Locally (Windows / Git Bash)

```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
python app.py
```

Once the server is running, open `http://localhost:10000` in your browser.

## Building the JavaScript Bundle
The JavaScript source for the public pages lives in `static/js/landing.js`. To regenerate the minified bundle (`static/js/landing.min.js`), install the development dependencies and run the build script:
```bash
python -m pip install -r requirements-dev.txt
python build_static.py
```

## Serving Static Assets from a CDN (Optional)
To load static assets from a CDN, set the `STATIC_CDN_URL` environment variable to the base URL of your CDN, for example `https://cdn.example.com/static`.
Before enabling it, make sure the entire contents of the `static/` folder have been uploaded to the CDN with the same directory structure, including `js/dashboard.js`, the `logo/` folder, and `favicon.svg`.

If `STATIC_CDN_URL` is not set, the application serves assets directly through Flask.