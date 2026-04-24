# Quak File Transfer

Quak File Transfer is a simple, lightweight web application built with Flask to share and download files from a specific folder on your local network. It provides a clean web interface to browse directories, download individual files, or download entire folders as a ZIP archive.

## Features

*   Web-based file and folder browser.
*   Download individual files.
*   Download entire folders as a single ZIP archive on-the-fly.
*   Human-readable file sizes (e.g., KB, MB, GB).
*   File type specific icons for easy identification.
*   Breadcrumb navigation for easy traversal of directories.
*   Guards against path traversal attacks.

## Requirements

*   Python 3.x
*   Flask

## Setup & Configuration

1.  **Install Dependencies:**
    Install the required Python package using pip.
    ```bash
    pip install Flask flask-cloudflared
    ```

## Running the Application

You can run the server directly using Python:

```bash
python app.py
```

The server will start, and by default, it will be accessible on port 5000 from any device on your network.

## Usage

Once the server is running, open a web browser on any device on the same network and navigate to:

`http://<your-server-ip>:5000`

Replace `<your-server-ip>` with the local IP address of the machine running the application (e.g., `192.168.1.10`). The first time you load the page, you will be prompted via a web interface to enter the absolute path of the folder you wish to share. Once successfully submitted, you can begin browsing and downloading.