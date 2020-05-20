import os

from flask import Flask, flash, render_template, request, redirect, url_for
from transmission_rpc import Client
from werkzeug.utils import secure_filename

from .constants import APP_PATH, SERVER, TORRENT_UPLOAD_DIR, TRANSMISSION_PORT
from .credentials import TRANSMISSION_USER, TRANSMISSION_PASS

app = Flask(__name__)
app.secret_key = b"SE#*ra83((!)~ra**&@(87rsmvmqef8*"


def transmission_client():
    return Client(host=SERVER, port=TRANSMISSION_PORT)


def transmission_web_url():
    host_without_port = request.host.split(":")[0]
    return f"http://{host_without_port}:{TRANSMISSION_PORT}"


def downloads_redirect(filename=""):
    return redirect(f"/files/{filename}")


def flash_exception(e, msg="Whoops, an error occured"):
    flash(f"{msg}. Please report this", "danger")
    flash(str(e), "danger")


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return home_get()
    if request.method == "POST":
        return home_post()


@app.route("/downloads/<torrent_id>", methods=["GET"])
def get_file(torrent_id):
    client = transmission_client()
    torrent = client.get_torrent(torrent_id)
    files = torrent.files()

    # If there is only one file in the torrent, send that
    if len(files) == 1:
        for f in files.values():
            filename = f["name"]
            return downloads_redirect(filename)

    # If all files are in the same dir, go to that dir's index
    directory = ""
    for f in files.values():
        filename = f["name"]
        split = filename.split("/")
        if len(split) < 2:
            break

        if not directory:
            directory = split[0]
        elif directory != split[0]:
            break
    if directory:
        return downloads_redirect(directory)

    # As a last resort, redirect to root index of all files
    return downloads_redirect()


@app.route("/downloads/<torrent_id>/delete", methods=["POST"])
def delete_file(torrent_id):
    client = transmission_client()

    try:
        client.remove_torrent(torrent_id, delete_data=True)
        flash("torrent and data deleted successfully", "success")
    except Exception as e:
        flash_exception(e, "Failed to remove torrent")

    return redirect(url_for("home"))


def home_get():
    torrents = []
    err = None
    try:
        torrents = transmission_client().get_torrents()
    except Exception as e:
        flash_exception(e)

    complete = [t for t in torrents if t.progress == 100.0]
    active = [t for t in torrents if t.progress != 100.0]

    return render_template(
        "home.html",
        complete=complete,
        active=active,
        transmission_web_url=transmission_web_url(),
        round=round,
    )


def home_post():
    client = transmission_client()

    if "magnet" in request.form:
        success = add_torrent_via_magnet(client)
    elif "file" in request.files:
        success = add_torrent_via_file(client)
    else:
        flash("Unrecognized request, please report this error", "danger")
        success = False

    if success:
        flash("torrent added successfully!", "success")

    return redirect(url_for("home"))


def add_torrent_via_magnet(client):
    """Return True on success """
    if not request.form["magnet"]:
        flash("magnet link empty", "warning")
    else:
        try:
            client.add_torrent(request.form["magnet"])
            return True
        except:
            flash("magnet link invalid", "warning")

    return False


def add_torrent_via_file(client):
    """Return True on success """
    torrent_file = request.files["file"]
    if not torrent_file.filename:
        flash(
            "No file selected", "warning",
        )
        return False

    if not torrent_file.filename.endswith(".torrent"):
        flash(
            "file must have a .torrent extension.", "warning",
        )
        return False

    filename = secure_filename(torrent_file.filename)
    file_save_location = os.path.join(TORRENT_UPLOAD_DIR, filename)
    torrent_file.save(file_save_location)

    success = True
    try:
        with open(file_save_location, "rb") as f:
            client.add_torrent(f)
    except:
        flash("Failed to add torrent by file", "warning")
        success = False

    # Once torrent is added, we no longer need the torrent file
    try:
        os.remove(file_save_location)
    except OSError:
        pass

    return success


if __name__ == "__main__":
    app.run()
