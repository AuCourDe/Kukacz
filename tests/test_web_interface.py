import io

import pytest

from app.processing_queue import ProcessingQueue
from app.web_interface import create_web_app


class DummyProcessor:
    def __init__(self, processed_dir, output_dir):
        self.processed_folder = processed_dir
        self.output_dir = output_dir

    def process_audio_file(self, audio_file_path, queue_item_id=None):
        timestamp = "20250101010101"
        transcript = self.output_dir / f"{audio_file_path.stem} {timestamp}.txt"
        analysis = self.output_dir / f"{audio_file_path.stem} ANALIZA {timestamp}.txt"
        transcript.write_text("transkrypcja")
        analysis.write_text("analiza")
        processed = self.processed_folder / f"{audio_file_path.stem} {timestamp}{audio_file_path.suffix}"
        processed.write_text("audio")
        return {
            "success": True,
            "timestamp": timestamp,
            "transcription_file": transcript.name,
            "analysis_file": analysis.name,
            "processed_audio": str(processed),
        }


@pytest.fixture
def web_context(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    processed_dir = tmp_path / "processed"
    input_dir.mkdir()
    output_dir.mkdir()
    processed_dir.mkdir()

    processor = DummyProcessor(processed_dir, output_dir)
    queue = ProcessingQueue()
    app = create_web_app(
        processor=processor,
        processing_queue=queue,
        input_folder=input_dir,
        output_folder=output_dir,
        asynchronous=False,
    )
    app.config["TESTING"] = True
    return app, queue


def test_dashboard_requires_login(web_context):
    app, _ = web_context
    response = app.test_client().get("/")
    assert response.status_code == 302


def test_upload_rejects_invalid_extension(web_context):
    app, queue = web_context
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["authenticated"] = True

    data = {"files": (io.BytesIO(b"test"), "document.txt")}
    response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)

    assert "Pominięto pliki" in response.get_data(as_text=True)
    assert queue.serialize() == []


def test_upload_audio_triggers_processing(web_context):
    app, queue = web_context
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["authenticated"] = True

    data = {"files": (io.BytesIO(b"audio"), "conversation.mp3")}
    response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200

    items = queue.serialize()
    assert len(items) == 1
    assert items[0]["status"] == "completed"
    assert "transcription" in items[0]["result_files"]

