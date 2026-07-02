import json
import requests
from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"

VIDEO_FIELDS = (
    "files(id,name,mimeType,thumbnailLink,size,videoMediaMetadata,modifiedTime),"
    "nextPageToken"
)


def _drive_request(params):
    """Call the Google Drive v3 files.list endpoint with our server-side key."""
    if not settings.GOOGLE_API_KEY:
        return None, "GOOGLE_API_KEY is not set on the server. Add it as an environment variable."
    params = {**params, "key": settings.GOOGLE_API_KEY}
    resp = requests.get(DRIVE_FILES_URL, params=params, timeout=15)
    data = resp.json()
    if "error" in data:
        return None, data["error"].get("message", "Unknown Google Drive API error")
    return data, None


def _list_all(folder_id):
    """Paginate through every file/folder inside folder_id."""
    all_files = []
    page_token = None
    while True:
        params = {
            "q": f"'{folder_id}' in parents and trashed = false",
            "fields": VIDEO_FIELDS,
            "pageSize": 200,
            "orderBy": "folder,name_natural",
        }
        if page_token:
            params["pageToken"] = page_token
        data, err = _drive_request(params)
        if err:
            raise RuntimeError(err)
        all_files.extend(data.get("files", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return all_files


SUPPORTED_MEDIA_TYPES = ('video/', 'audio/')

def _split(files):
    folders = [f for f in files if f["mimeType"] == "application/vnd.google-apps.folder"]
    videos  = [f for f in files if any(f.get("mimeType", "").startswith(t) for t in SUPPORTED_MEDIA_TYPES)]
    return folders, videos


@require_GET
def root_folder(request):
    """Convenience endpoint: returns the configured root folder id."""
    return JsonResponse({"root_folder_id": settings.DRIVE_ROOT_FOLDER_ID})


@require_GET
def list_folder(request, folder_id):
    try:
        files = _list_all(folder_id)
    except RuntimeError as e:
        return JsonResponse({"error": str(e)}, status=502)
    folders, videos = _split(files)
    return JsonResponse({"folders": folders, "videos": videos})


@require_GET
def file_detail(request, file_id):
    """Metadata for a single file — used by the standalone player page."""
    if not settings.GOOGLE_API_KEY:
        return JsonResponse({"error": "GOOGLE_API_KEY is not set on the server."}, status=500)
    url = f"{DRIVE_FILES_URL}/{file_id}"
    params = {
        "key": settings.GOOGLE_API_KEY,
        "fields": "id,name,mimeType,size,videoMediaMetadata,thumbnailLink,description,modifiedTime",
    }
    resp = requests.get(url, params=params, timeout=15)
    data = resp.json()
    if "error" in data:
        return JsonResponse({"error": data["error"].get("message", "Drive error")}, status=502)
    return JsonResponse(data)


@require_GET
def search_videos(request):
    """
    Recursively search ALL videos under the root folder by name.
    Used by the standalone player page's "browse all videos" list and search box.
    Query param: ?q=keyword (optional, empty = list everything)
    """
    query_text = request.GET.get("q", "").strip()
    root = settings.DRIVE_ROOT_FOLDER_ID
    if not root:
        return JsonResponse({"error": "DRIVE_ROOT_FOLDER_ID is not set on the server."}, status=500)

    videos = []
    try:
        # Breadth-first walk through all subfolders, collecting videos
        to_visit = [root]
        visited = set()
        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue
            visited.add(current)
            files = _list_all(current)
            folders, vids = _split(files)
            videos.extend(vids)
            to_visit.extend(f["id"] for f in folders)
    except RuntimeError as e:
        return JsonResponse({"error": str(e)}, status=502)

    if query_text:
        q_lower = query_text.lower()
        videos = [v for v in videos if q_lower in v["name"].lower()]

    return JsonResponse({"videos": videos, "count": len(videos)})


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@csrf_exempt
@require_GET
def stream_file(request, file_id):
    """
    Sends the browser's <video> element directly to Google Drive's own media
    URL via an HTTP redirect, instead of relaying every video byte through
    this server. Google's own servers handle Range requests (seeking) and
    bandwidth far better than a small free-tier backend ever could, so this
    fixes slow starts and mid-playback buffering stalls.
    """
    if not settings.GOOGLE_API_KEY:
        return HttpResponse("GOOGLE_API_KEY not configured on server.", status=500)
    url = f"{DRIVE_FILES_URL}/{file_id}?alt=media&key={settings.GOOGLE_API_KEY}"
    return HttpResponseRedirect(url)
