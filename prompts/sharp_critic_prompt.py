import os


def get_sharp_critic_prompt(
    sharpness_score: float,
    brightness_val: float,
    contrast_val: float
) -> str:
    """获取锐评版提示词（从 MD 文件加载）"""
    prompt_path = os.path.join(
        os.path.dirname(__file__),
        "sharp_critic.md"
    )

    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    return template.format(
        sharpness_score=sharpness_score,
        brightness_val=brightness_val,
        contrast_val=contrast_val
    )