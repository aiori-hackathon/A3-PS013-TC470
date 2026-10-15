"""Tests for the SHA-256 evidence-hashing utilities (PROJECT_PLAN.md
section 2: "preserve evidence and calculate SHA-256 hashes")."""
import hashlib

from app.security import sha256_of_bytes, sha256_of_file


def test_sha256_of_bytes_matches_known_digest():
    data = b"CyberTrace evidence integrity test"
    expected = hashlib.sha256(data).hexdigest()
    assert sha256_of_bytes(data) == expected


def test_sha256_of_file_matches_known_digest(tmp_path):
    content = b"line one\nline two\nline three\n"
    file_path = tmp_path / "sample.log"
    file_path.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()
    assert sha256_of_file(file_path) == expected


def test_sha256_of_file_detects_modification(tmp_path):
    """A changed file must produce a different hash -- the whole point of
    evidence integrity verification (PROJECT_PLAN.md section 8)."""
    file_path = tmp_path / "sample.log"
    file_path.write_bytes(b"original content")
    original_hash = sha256_of_file(file_path)

    file_path.write_bytes(b"tampered content")
    new_hash = sha256_of_file(file_path)

    assert original_hash != new_hash
