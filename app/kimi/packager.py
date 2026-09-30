from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

PACKAGE_FILES = (
    "manifest.json",
    "tasks.jsonl",
    "answers.jsonl",
    "sources.jsonl",
    "checksums.json",
)


def create_package(
        source_dir: str | Path,
        zip_path: str | Path,
) -> Path:
    source = Path(source_dir)
    target = Path(zip_path)

    if not source.exists():
        raise FileNotFoundError(
            f"打包目录不存在：{source}"
        )

    missing_files = [
        filename
        for filename in PACKAGE_FILES
        if not (source / filename).is_file()
    ]

    if missing_files:
        raise FileNotFoundError(
            "标准包缺少文件："
            + ", ".join(missing_files)
        )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with ZipFile(
            target,
            "w",
            compression=ZIP_DEFLATED,
    ) as zip_file:

        # 五个 GEO 标准基础文件
        for filename in PACKAGE_FILES:
            file_path = source / filename

            zip_file.write(
                file_path,
                arcname=filename,
            )

        # 截图作为标准包附加文件，
        # 保留 screenshots/<task_id>.png
        # 的包内相对路径。
        screenshots_dir = (
            source
            / "screenshots"
        )

        if screenshots_dir.is_dir():

            screenshot_files = sorted(
                path
                for path in screenshots_dir.rglob("*")
                if path.is_file()
            )

            for screenshot_file in screenshot_files:

                archive_path = (
                    screenshot_file
                    .relative_to(source)
                    .as_posix()
                )

                zip_file.write(
                    screenshot_file,
                    arcname=archive_path,
                )

    return target
