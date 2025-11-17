#!/usr/bin/env python3
"""
Moduł z prostym interfejsem Flask do dodawania i podglądu plików.
"""
from __future__ import annotations

import logging
import threading
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from .audio_processor import AudioProcessor
from .config import (
    INPUT_FOLDER,
    OUTPUT_FOLDER,
    WEB_HOST,
    WEB_LOGIN,
    WEB_PASSWORD,
    WEB_PORT,
    WEB_SECRET_KEY,
)
from .file_loader import AudioFileValidator
from .processing_queue import ProcessingQueue, QueueItem

logger = logging.getLogger(__name__)


def create_web_app(
    processor: AudioProcessor,
    processing_queue: ProcessingQueue,
    *,
    input_folder: Optional[Path] = None,
    output_folder: Optional[Path] = None,
    asynchronous: bool = True,
) -> Flask:
    """
    Buduje i konfiguruje aplikację Flask.
    """

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=None,
    )
    app.config["SECRET_KEY"] = WEB_SECRET_KEY

    target_input = Path(input_folder or INPUT_FOLDER)
    target_input.mkdir(parents=True, exist_ok=True)
    target_output = Path(output_folder or OUTPUT_FOLDER)
    target_output.mkdir(parents=True, exist_ok=True)

    allowed_extensions = sorted(
        AudioFileValidator.SUPPORTED_EXTENSIONS
    )
    accept_attribute = ",".join(allowed_extensions)

    status_labels: Dict[str, str] = {
        "queued": "Oczekuje",
        "processing": "W trakcie",
        "completed": "Zakończone",
        "failed": "Błąd",
    }

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("authenticated"):
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)

        return wrapped

    def _start_processing(queue_item: QueueItem) -> None:
        """Uruchamia przetwarzanie pliku (w tle lub synchronicznie)."""

        def _worker():
            try:
                processing_queue.mark_processing(queue_item.id)
                result = processor.process_audio_file(
                    queue_item.input_path,
                    queue_item_id=queue_item.id,
                )
                if result.get("success"):
                    manual_files: Dict[str, str] = {}
                    transcription_file = result.get("transcription_file")
                    analysis_file = result.get("analysis_file")
                    processed_audio = result.get("processed_audio")
                    if transcription_file:
                        manual_files["transcription"] = transcription_file
                    if analysis_file:
                        manual_files["analysis"] = analysis_file
                    if processed_audio:
                        processed_name = (
                            Path(processed_audio).name
                            if isinstance(processed_audio, str)
                            else processed_audio
                        )
                        manual_files["processed_audio"] = processed_name
                    if manual_files:
                        processing_queue.mark_completed(queue_item.id, manual_files)
                else:
                    processing_queue.mark_failed(
                        queue_item.id,
                        "Przetwarzanie nie zwróciło wyników.",
                    )
            except Exception as exc:  # pragma: no cover
                logger.error("Błąd podczas przetwarzania w tle: %s", exc)
                processing_queue.mark_failed(queue_item.id, str(exc))

        if asynchronous:
            threading.Thread(target=_worker, daemon=True).start()
        else:
            _worker()

    def _save_file(storage, destination_dir: Path) -> Optional[Path]:
        filename = secure_filename(storage.filename or "")
        if not filename:
            return None

        suffix = Path(filename).suffix.lower()
        if suffix not in AudioFileValidator.SUPPORTED_EXTENSIONS:
            return None

        destination_dir.mkdir(parents=True, exist_ok=True)
        candidate = destination_dir / filename
        counter = 1
        while candidate.exists():
            candidate = destination_dir / f"{Path(filename).stem}_{counter}{suffix}"
            counter += 1

        storage.save(candidate)
        return candidate

    @app.context_processor
    def inject_globals():
        return {
            "status_labels": status_labels,
            "allowed_extensions": [ext.lstrip(".") for ext in allowed_extensions],
        }

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if username == WEB_LOGIN and password == WEB_PASSWORD:
                session["authenticated"] = True
                flash("Zalogowano pomyślnie.", "success")
                return redirect(request.args.get("next") or url_for("dashboard"))
            flash("Niepoprawny login lub hasło.", "error")
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        session.clear()
        flash("Wylogowano.", "info")
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def dashboard():
        queue_items = processing_queue.serialize()
        return render_template(
            "dashboard.html",
            queue_items=queue_items,
            accept_attribute=accept_attribute,
            estimated_hint="Szacowany czas: ok. 1 minuta na 1 MB pliku.",
        )

    @app.route("/upload", methods=["POST"])
    @login_required
    def upload():
        files = request.files.getlist("files")
        if not files or all(not file.filename for file in files):
            flash("Nie wybrano żadnych plików.", "error")
            return redirect(url_for("dashboard"))

        saved_items: List[QueueItem] = []
        rejected: List[str] = []

        for storage in files:
            saved_path = _save_file(storage, target_input)
            if not saved_path:
                rejected.append(storage.filename or "bez_nazwy")
                continue

            queue_item = processing_queue.enqueue(saved_path)
            saved_items.append(queue_item)
            _start_processing(queue_item)

        if saved_items:
            total_estimate = sum(item.estimated_minutes for item in saved_items)
            flash(
                f"Przesłano {len(saved_items)} plików. "
                f"Szacowany łączny czas: ~{total_estimate} min.",
                "success",
            )
        if rejected:
            flash(
                f"Pominięto pliki z nieobsługiwanymi rozszerzeniami: {', '.join(rejected)}",
                "warning",
            )

        return redirect(url_for("dashboard"))

    @app.route("/queue.json")
    @login_required
    def queue_json():
        return jsonify({"items": processing_queue.serialize()})

    @app.route("/download/<queue_id>/<file_type>")
    @login_required
    def download_result(queue_id: str, file_type: str):
        file_name = processing_queue.get_result_file(queue_id, file_type)
        if not file_name:
            abort(404)

        if file_type in {"transcription", "analysis"}:
            directory = target_output
        elif file_type == "processed_audio":
            directory = processor.processed_folder
        else:
            abort(404)

        return send_from_directory(directory, file_name, as_attachment=True)

    logger.info(
        "Interfejs webowy gotowy. Logowanie: %s / %s. Host: %s:%s",
        WEB_LOGIN,
        "***",
        WEB_HOST,
        WEB_PORT,
    )

    return app


__all__ = ["create_web_app"]

