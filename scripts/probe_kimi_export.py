import json
from pathlib import Path

from app.kimi.checkpoint import KimiCheckpointStore
from app.kimi.exporter import KimiExporter

BATCH_ID = "kimi_w6_geo_sources_002"

CHECKPOINT_ROOT = (
        Path("output")
        / "checkpoints"
)

OUTPUT_DIR = (
        Path("output")
        / "package"
        / BATCH_ID
)


def main() -> None:
    store = KimiCheckpointStore(
        root_dir=CHECKPOINT_ROOT,
        batch_id=BATCH_ID,
    )

    result_files = sorted(
        store.results_dir.glob("*.json")
    )

    results = []

    for path in result_files:
        result = store.load_result(
            path.stem
        )

        if result is not None:
            results.append(
                result
            )

    with store.meta_path.open(
            "r",
            encoding="utf-8",
    ) as file:
        meta = json.load(
            file
        )

    print(
        "RESULT COUNT:",
        len(results),
    )

    exporter = KimiExporter()

    exporter.export(
        results=results,
        output_dir=str(OUTPUT_DIR),
        started_at=(
            meta.get("started_at", "")
        ),
        finished_at=(
            meta.get("finished_at", "")
        ),
    )

    print(
        "OUTPUT:",
        OUTPUT_DIR.resolve(),
    )

    for path in sorted(
            OUTPUT_DIR.iterdir()
    ):
        print(
            path.name,
            path.stat().st_size,
        )


if __name__ == "__main__":
    main()
