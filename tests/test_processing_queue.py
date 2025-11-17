from app.processing_queue import ProcessingQueue


def test_enqueue_sets_estimate(tmp_path):
    audio = tmp_path / "call.mp3"
    audio.write_bytes(b"0" * 3 * 1024 * 1024)  # 3 MB

    queue = ProcessingQueue()
    item = queue.enqueue(audio)

    assert item.estimated_minutes == 3
    serialized = queue.serialize()
    assert serialized[0]["status"] == "queued"
    assert serialized[0]["filename"] == "call.mp3"


def test_mark_completed_updates_status(tmp_path):
    audio = tmp_path / "call2.mp3"
    audio.write_text("audio")

    queue = ProcessingQueue()
    item = queue.enqueue(audio)
    queue.mark_processing(item.id)
    queue.mark_completed(
        item.id,
        {"transcription": "call2 20250101010101.txt", "analysis": "call2 ANALIZA 20250101010101.txt"},
    )

    serialized = queue.serialize()[0]
    assert serialized["status"] == "completed"
    assert serialized["result_files"]["transcription"].endswith(".txt")

