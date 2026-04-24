import os
import shutil
import tempfile
from flask import Flask, send_file, abort, render_template, redirect, url_for, request
from flask_cloudflared import run_with_cloudflared

app = Flask(__name__)
run_with_cloudflared(app)
app.config['SHARE_PATH'] = None


def human_size(num_bytes):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def icon_type_for(name, is_dir):
    if is_dir:
        return 'folder'
    ext = os.path.splitext(name)[1].lower()
    if ext == '.pdf':
        return 'pdf'
    if ext in ('.epub', '.mobi', '.azw', '.azw3', '.fb2'):
        return 'epub'
    if ext in ('.doc', '.docx', '.odt', '.rtf'):
        return 'doc'
    if ext in ('.txt', '.md', '.rst'):
        return 'text'
    if ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'):
        return 'image'
    if ext in ('.zip', '.rar', '.7z', '.tar', '.gz'):
        return 'archive'
    return 'file'


def safe_path(subpath):
    """Resolve subpath inside SHARE_PATH and guard against path traversal."""
    share_path = app.config['SHARE_PATH']
    if subpath:
        joined = os.path.normpath(os.path.join(share_path, subpath))
    else:
        joined = share_path
    # Must still start with SHARE_PATH
    if not joined.startswith(share_path):
        abort(403)
    return joined


@app.before_request
def require_setup():
    # Redirect to setup if SHARE_PATH is not yet configured
    if not app.config.get('SHARE_PATH') and request.endpoint and request.endpoint not in ('setup', 'static'):
        return redirect(url_for('setup'))


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    error = None
    if request.method == 'POST':
        path = request.form.get('path', '').strip()
        if os.path.isdir(path):
            app.config['SHARE_PATH'] = os.path.normpath(path)
            return redirect(url_for('index'))
        else:
            error = "The provided path is not a valid directory. Please try again."
    return render_template('setup.html', error=error)


@app.route('/')
def index():
    return redirect(url_for('browse', subpath=''))


@app.route('/browse/', defaults={'subpath': ''})
@app.route('/browse/<path:subpath>')
def browse(subpath):
    target = safe_path(subpath)

    if not os.path.exists(target):
        abort(404)
    if not os.path.isdir(target):
        # If someone navigates to a file URL, just download it
        return redirect(url_for('download', subpath=subpath))

    raw_entries = []
    try:
        raw_entries = list(os.scandir(target))
    except PermissionError:
        abort(403)

    raw_entries.sort(key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.lower()))

    items = []
    total_bytes = 0
    folder_count = file_count = 0

    for e in raw_entries:
        rel = os.path.relpath(e.path, app.config['SHARE_PATH']).replace('\\', '/')
        is_dir = e.is_dir(follow_symlinks=False)
        itype = icon_type_for(e.name, is_dir)

        if is_dir:
            folder_count += 1
            meta = 'Folder'
            size_str = '—'
        else:
            file_count += 1
            try:
                sz = e.stat().st_size
                total_bytes += sz
                size_str = human_size(sz)
            except OSError:
                size_str = '?'
            meta = size_str

        items.append(dict(
            name=e.name,
            rel_path=rel,
            is_dir=is_dir,
            icon_type=itype,
            meta=meta,
        ))

    # Build breadcrumb parts
    parts = [p for p in subpath.replace('\\', '/').split('/') if p]
    breadcrumbs = []
    for i, part in enumerate(parts):
        breadcrumbs.append({
            'name': part,
            'path': '/'.join(parts[:i + 1]),
        })

    return render_template(
        'browse.html',
        items=items,
        breadcrumbs=breadcrumbs,
        folder_count=folder_count,
        file_count=file_count,
        total_size=human_size(total_bytes),
        share_path=app.config['SHARE_PATH'],
    )


@app.route('/download/<path:subpath>')
def download(subpath):
    target = safe_path(subpath)

    if not os.path.exists(target):
        abort(404)

    if os.path.isdir(target):
        # Zip the folder into a proper temp file then send
        tmp_dir = tempfile.mkdtemp()
        try:
            base_name = os.path.join(tmp_dir, os.path.basename(target))
            zip_path = shutil.make_archive(
                base_name=base_name,
                format='zip',
                root_dir=os.path.dirname(target),   # parent of the folder
                base_dir=os.path.basename(target),  # folder name itself
            )
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=f"{os.path.basename(target)}.zip",
                mimetype='application/zip',
            )
        except Exception as e:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            abort(500, str(e))

    # Plain file download
    return send_file(
        target,
        as_attachment=True,
        download_name=os.path.basename(target),
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)