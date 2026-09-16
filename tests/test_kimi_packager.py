from pathlib import Path
from zipfile import ZipFile

from app.kimi.packager import (
    PACKAGE_FILES,
    create_package,
)


def test_create_package_contains_only_standard_files(
        tmp_path: Path,
):
    source_dir = (
            tmp_path
            / "package"
    )

    source_dir.mkdir()

    for filename in PACKAGE_FILES:
        (
                source_dir
                / filename
        ).write_text(
            "test",
            encoding="utf-8",
        )

    # 故意放一个额外文件，
    # 确保它不会被打进 ZIP。
    (
            source_dir
            / "debug.txt"
    ).write_text(
        "should not be packaged",
        encoding="utf-8",
    )

    zip_path = (
            tmp_path
            / "package.zip"
    )

    result = create_package(
        source_dir=source_dir,
        zip_path=zip_path,
    )

    assert result == zip_path
    assert zip_path.is_file()

    with ZipFile(
            zip_path,
            "r",
    ) as zip_file:
        names = zip_file.namelist()

    assert names == list(
        PACKAGE_FILES
    )


def test_create_package_missing_file_fails(
        tmp_path: Path,
):
    source_dir = (
            tmp_path
            / "package"
    )

    source_dir.mkdir()

    # 少写一个标准文件
    for filename in PACKAGE_FILES[:-1]:
        (
                source_dir
                / filename
        ).write_text(
            "test",
            encoding="utf-8",
        )

    zip_path = (
            tmp_path
            / "package.zip"
    )

    try:
        create_package(
            source_dir=source_dir,
            zip_path=zip_path,
        )

    except FileNotFoundError:
        pass

    else:
        raise AssertionError(
            "缺少标准文件时应抛出 "
            "FileNotFoundError"
        )
