from infra.main import bucket


def test_bucket_id() -> None:
    assert bucket.id is not None
