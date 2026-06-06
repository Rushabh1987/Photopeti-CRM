"""Folder watcher (Phase 3). A watchdog observer on settings.watch_folder; on a
new video file (by extension) it creates an EditingTask(status="waiting").
Runs in a background thread started from app.main's lifespan.

Note: only sees files on the machine where they physically land — run the app
(or at least this component) on the PC that receives the camera/phone uploads.
"""
# TODO(Phase 3): start_watcher() / stop_watcher()
