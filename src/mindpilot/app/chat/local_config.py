from pathlib import Path


LOCAL_MODELS = {
    **{f"Qwen2.5-{size}-Instruct": f"Qwen/Qwen2.5-{size}-Instruct"
       for size in ("0.5B", "1.5B", "3B", "7B", "14B", "32B", "72B")},
    "Qwen2.5-Coder-32B-Instruct": "Qwen/Qwen2.5-Coder-32B-Instruct",
    "QwQ-32B-Preview": "Qwen/QwQ-32B-Preview",
    "Qwen2-0.5B": "Qwen/Qwen2-0.5B-Instruct",
    "MiniCPM-2B": "openbmb/MiniCPM-2B-dpo-bf16",
}


def resolve_model_path(model_name: str) -> str:
    if model_name in LOCAL_MODELS:
        return LOCAL_MODELS[model_name]
    if model_name in LOCAL_MODELS.values():
        return model_name
    path = Path(model_name).expanduser()
    if path.is_dir() and (path / "config.json").is_file():
        return str(path.resolve())
    raise ValueError(f"请选择支持的本地模型，或包含 config.json 的模型目录：{model_name}")


def generation_options(temperature: float, max_tokens: int) -> dict:
    if not 0 <= temperature <= 2:
        raise ValueError("temperature 必须在 0 到 2 之间")
    if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ValueError("max_tokens 必须是正整数")
    options = {"max_new_tokens": max_tokens, "do_sample": temperature > 0}
    if temperature > 0:
        options.update(temperature=temperature, top_p=0.9)
    return options


def truncate_at_stop(text: str, stop: list[str] | None) -> str:
    positions = [text.index(token) for token in stop or [] if token and token in text]
    return text[:min(positions)] if positions else text
