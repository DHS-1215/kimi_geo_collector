from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.kimi.checksum import generate_checksums
from app.kimi.geo_contract import (
    COLLECTOR_VERSION,
    GEO_BATCH_VERSION,
    GEO_SCHEMA_VERSION,
    KIMI_PLATFORM_CODE,
    KIMI_PLATFORM_NAME,
    build_answer_id,
    build_occurrence_id,
    resolve_product,
)
from app.kimi.result import KimiCollectionResult


class KimiExporter:

    def export(
            self,
            results: list[KimiCollectionResult],
            output_dir: str,
            started_at: str = "",
            finished_at: str = "",
    ) -> None:

        output = Path(output_dir)

        output.mkdir(
            parents=True,
            exist_ok=True,
        )

        # 清理旧版中间产物，避免标准目录中
        # 残留 answers.json / sources.json。
        for legacy_filename in (
                "answers.json",
                "sources.json",
        ):
            legacy_path = (
                    output
                    / legacy_filename
            )

            if legacy_path.exists():
                legacy_path.unlink()

        # 将采集阶段保存的截图复制到
        # GEO 标准包 screenshots/ 目录。
        screenshot_files = self._copy_screenshots(
            results,
            output,
        )

        # GEO v1 标准数据文件
        self._save_tasks_jsonl(
            results,
            output / "tasks.jsonl",
        )

        self._save_answers_jsonl(
            results,
            output / "answers.jsonl",
        )

        self._save_sources_jsonl(
            results,
            output / "sources.jsonl",
        )

        self._save_manifest(
            results,
            output / "manifest.json",
            started_at=started_at,
            finished_at=finished_at,
        )

        # checksums.json 不计算自身 checksum。
        checksum_files = [
            output / "manifest.json",
            output / "tasks.jsonl",
            output / "answers.jsonl",
            output / "sources.jsonl",
            *screenshot_files,
        ]

        checksums = generate_checksums(
            checksum_files,
            base_dir=output,
        )

        self._write_json(
            output / "checksums.json",
            checksums,
        )

    def _copy_screenshots(
            self,
            results: list[KimiCollectionResult],
            output: Path,
    ) -> list[Path]:
        """
        将采集阶段截图复制到 GEO 标准包。

        标准包结构：
        screenshots/<task_id>.png
        """

        screenshots_dir = (
                output
                / "screenshots"
        )

        copied_files: list[Path] = []

        # 如果重复导出同一个 batch，
        # 先清理旧截图，避免残留。
        if screenshots_dir.exists():
            shutil.rmtree(
                screenshots_dir
            )

        for result in results:

            # 先清空 package 相对路径。
            # 只有真正复制成功后才重新赋值。
            result.screenshot_path = ""

            local_path_raw = (
                    result.screenshot_local_path
                    or ""
            ).strip()

            # 本任务没有截图时直接跳过。
            if not local_path_raw:
                continue

            source = Path(
                local_path_raw
            )

            if not source.is_file():
                if not result.screenshot_error:
                    result.screenshot_error = (
                        "截图文件不存在："
                        f"{source}"
                    )

                continue

            screenshots_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            target = (
                    screenshots_dir
                    / f"{result.task_id}.png"
            )

            try:
                shutil.copy2(
                    source,
                    target,
                )
            except Exception as e:
                if not result.screenshot_error:
                    result.screenshot_error = (
                        "复制截图失败："
                        f"{e}"
                    )

                continue

            # 这里写的是 ZIP / GEO 标准包内部路径，
            # 不是 Windows 本机路径。
            result.screenshot_path = (
                f"screenshots/"
                f"{result.task_id}.png"
            )

            copied_files.append(
                target
            )

        return copied_files

    def _save_tasks_jsonl(
            self,
            results: list[KimiCollectionResult],
            path: Path,
    ) -> None:

        rows = []

        for result in results:
            rows.append(
                {
                    "task_id": result.task_id,
                    "batch_id": result.batch_id,
                    "platform_code": KIMI_PLATFORM_CODE,
                    "question_id": result.question_id,
                    "question": result.question,
                    "mode_code": result.mode_code,
                    "task_status": result.status,
                    "error_code": None,
                    "error_message": (
                            result.error
                            or None
                    ),
                }
            )

        self._write_jsonl(
            path,
            rows,
        )

    def _save_answers_jsonl(
            self,
            results: list[KimiCollectionResult],
            path: Path,
    ) -> None:

        rows = []

        for result in results:
            answer_id = build_answer_id(
                batch_id=result.batch_id,
                task_id=result.task_id,
            )

            platform_meta = {
                "model": result.model,
                "raw_mode": result.mode,
                "conversation_url": result.conversation_url,
            }

            if result.source_error:
                platform_meta[
                    "source_error"
                ] = result.source_error

            if result.screenshot_path:
                platform_meta[
                    "screenshot_sha256"
                ] = result.screenshot_sha256

                platform_meta[
                    "screenshot_size_bytes"
                ] = result.screenshot_size_bytes

                platform_meta[
                    "screenshot_width"
                ] = result.screenshot_width

                platform_meta[
                    "screenshot_height"
                ] = result.screenshot_height

            if result.screenshot_error:
                platform_meta[
                    "screenshot_error"
                ] = result.screenshot_error

            rows.append(
                {
                    "answer_id": answer_id,
                    "task_id": result.task_id,
                    "question_id": result.question_id,
                    "mode_code": result.mode_code,
                    "question_text": result.question,
                    "answer_text_raw": result.answer,
                    "answer_text_clean": (
                        result.answer.strip()
                        if result.answer
                        else ""
                    ),
                    "acquisition_status": (
                        result.acquisition_status
                    ),
                    "validation_status": (
                        result.validation_status
                    ),
                    "is_complete": (
                        result.is_complete
                    ),
                    "source_collection_status": (
                        result.source_collection_status
                    ),
                    "source_count_raw": (
                        result.source_count_raw
                    ),
                    "screenshot_path": (
                            result.screenshot_path
                            or None
                    ),
                    "platform_meta_json": (
                        platform_meta
                    ),
                    "collected_at": (
                            result.collected_at
                            or None
                    ),
                    "batch_id": (
                        result.batch_id
                    ),
                    "platform_code": (
                        KIMI_PLATFORM_CODE
                    ),
                }
            )

        self._write_jsonl(
            path,
            rows,
        )

    def _save_sources_jsonl(
            self,
            results: list[KimiCollectionResult],
            path: Path,
    ) -> None:

        rows = []

        for result in results:
            answer_id = build_answer_id(
                batch_id=result.batch_id,
                task_id=result.task_id,
            )

            seen_urls: set[str] = set()

            for source in result.sources:
                source_url_raw = (
                    source.url.strip()
                )

                # 中央标准 source_url_raw
                # 不能为空。
                if not source_url_raw:
                    continue

                is_duplicate = (
                        source_url_raw
                        in seen_urls
                )

                seen_urls.add(
                    source_url_raw
                )

                source_order = (
                    source.index
                )

                occurrence_id = (
                    build_occurrence_id(
                        batch_id=result.batch_id,
                        answer_id=answer_id,
                        source_order=source_order,
                        source_url_raw=source_url_raw,
                    )
                )

                rows.append(
                    {
                        "answer_id": answer_id,
                        "source_order": source_order,
                        "source_url_raw": (
                            source_url_raw
                        ),
                        "source_title_raw": (
                                source.title
                                or None
                        ),
                        "source_site_name_raw": (
                                source.source
                                or None
                        ),
                        "source_snippet": (
                                source.description
                                or None
                        ),
                        "is_duplicate_in_answer": (
                            is_duplicate
                        ),
                        "occurrence_id": (
                            occurrence_id
                        ),
                    }
                )

        self._write_jsonl(
            path,
            rows,
        )

    def _write_jsonl(
            self,
            path: Path,
            rows,
    ) -> None:

        with open(
                path,
                "w",
                encoding="utf-8",
        ) as f:
            for row in rows:
                f.write(
                    json.dumps(
                        row,
                        ensure_ascii=False,
                    )
                )
                f.write("\n")

    def _save_answers(
            self,
            results: list[KimiCollectionResult],
            path: Path,
    ) -> None:

        data = []

        for result in results:
            data.append(
                {
                    "batch_id": result.batch_id,
                    "task_id": result.task_id,
                    "platform": result.platform,
                    "product": result.product,
                    "question": result.question,
                    "answer": result.answer,
                    "model": result.model,
                    "mode": result.mode,
                    "conversation_url": result.conversation_url,
                    "status": result.status,
                }
            )

        self._write_json(
            path,
            data,
        )

    def _save_sources(
            self,
            results: list[KimiCollectionResult],
            path: Path,
    ) -> None:

        data = []

        for result in results:
            data.append(
                {
                    "batch_id": result.batch_id,
                    "task_id": result.task_id,
                    "platform": result.platform,
                    "product": result.product,
                    "question": result.question,
                    "sources": [
                        {
                            "source": source.source,
                            "title": source.title,
                            "url": source.url,
                            "domain": source.domain,
                            "description": source.description,
                        }
                        for source in result.sources
                    ],
                }
            )

        self._write_json(
            path,
            data,
        )

    def _save_manifest(
            self,
            results: list[KimiCollectionResult],
            path: Path,
            started_at: str = "",
            finished_at: str = "",
    ) -> None:

        success = sum(
            1
            for result in results
            if result.status == "success"
        )

        failed = (
                len(results)
                - success
        )

        batch_id = (
            results[0].batch_id
            if results
            else ""
        )

        collection_modes = sorted(
            {
                result.mode_code
                for result in results
                if result.mode_code
            }
        )

        source_count = sum(
            1
            for result in results
            for source in result.sources
            if source.url.strip()
        )

        product_names = {
            result.product.strip()
            for result in results
            if result.product.strip()
        }

        if not product_names:
            raise ValueError(
                "导出 GEO 标准包时 "
                "product 不能为空"
            )

        if len(product_names) != 1:
            raise ValueError(
                "同一 GEO 标准包不能包含多个产品："
                + ", ".join(
                    sorted(product_names)
                )
            )

        product_id, product_name = (
            resolve_product(
                next(iter(product_names))
            )
        )

        manifest = {
            "schema_version": (
                GEO_SCHEMA_VERSION
            ),
            "geo_batch_version": (
                GEO_BATCH_VERSION
            ),

            "platform_code": (
                KIMI_PLATFORM_CODE
            ),
            "platform_name": (
                KIMI_PLATFORM_NAME
            ),

            "product_id": (
                product_id
            ),
            "product_name": (
                product_name
            ),

            "batch_id": batch_id,

            "collector_version": (
                COLLECTOR_VERSION
            ),

            "capabilities": {
                "supports_sources": True,
                "supports_multiple_modes": True,
                "supports_screenshot": True,
            },

            "status": (
                "PASS"
                if failed == 0
                else "PASS_WITH_WARNINGS"
            ),

            "task_count": len(results),
            "answer_count": len(results),
            "source_count": source_count,

            "success_tasks": success,
            "failed_tasks": failed,

            "collection_modes": (
                collection_modes
            ),
        }

        if started_at:
            manifest[
                "started_at"
            ] = started_at

        if finished_at:
            manifest[
                "finished_at"
            ] = finished_at

        self._write_json(
            path,
            manifest,
        )

    def _write_json(
            self,
            path: Path,
            data,
    ) -> None:

        with open(
                path,
                "w",
                encoding="utf-8",
        ) as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )
