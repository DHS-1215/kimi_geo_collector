from enum import StrEnum


class KimiMode(StrEnum):
    STANDARD = "标准"
    ADVANCED = "进阶"
    EXTREME = "极致"


class KimiModel(StrEnum):
    FAST = "快速"
    K3 = "K3"
    K3_CLUSTER = "K3 集群"


MODEL_MODE_COMPATIBILITY: dict[
    KimiModel,
    set[KimiMode],
] = {
    KimiModel.FAST: {
        KimiMode.STANDARD,
        KimiMode.ADVANCED,
    },

    KimiModel.K3: {
        KimiMode.STANDARD,
        KimiMode.ADVANCED,
        KimiMode.EXTREME,
    },

    KimiModel.K3_CLUSTER: {
        KimiMode.STANDARD,
        KimiMode.ADVANCED,
        KimiMode.EXTREME,
    },
}


def is_model_mode_compatible(
        model: KimiModel,
        mode: KimiMode,
) -> bool:
    return (
        mode
        in MODEL_MODE_COMPATIBILITY[
            model
        ]
    )