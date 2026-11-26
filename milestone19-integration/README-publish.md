# Milestone 21: atomic batch publication

Use `publish_batch.publish(source, destination, contract, required, key)` after staging a CSV. The destination directory must already exist. The function copies the input to a private temporary file in the destination directory, validates that snapshot using the existing gate, and atomically replaces the destination only on success. Rejected batches leave the previous output untouched. I/O errors propagate; temporary files are cleaned up. This is a local filesystem implementation, not an S3 transaction or a multi-writer lock. Concurrent publishers require external coordination; producers should finish writing before publication.

Run all tests from `milestone19-integration` with `python -m unittest discover -v`. No cloud credentials or dependencies are needed.
