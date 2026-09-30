import hashlib
from pathlib import Path


def calculate_sha256(
        file_path: str | Path,
) -> str:
    path = Path(file_path)

    sha256 = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


def generate_checksums(
        files: list[str | Path],
        base_dir: str | Path | None = None,
) -> dict[str, dict[str, str]]:
    file_checksums: dict[str, str] = {}

    base = (
        Path(base_dir).resolve()
        if base_dir is not None
        else None
    )

    for file in files:
        path = Path(file)

        if base is not None:
            try:
                checksum_key = (
                    path.resolve()
                    .relative_to(base)
                    .as_posix()
                )
            except ValueError:
                checksum_key = path.name
        else:
            checksum_key = path.name

        file_checksums[
            checksum_key
        ] = calculate_sha256(
            path
        )

    return {
        "files": file_checksums
    }
