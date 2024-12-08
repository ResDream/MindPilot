import os
from threading import RLock
from typing import Any, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from .local_config import generation_options, resolve_model_path, truncate_at_stop


_model_lock = RLock()
_cached_model = None
_cached_path = None


def load_local_model(model_path: str, cache_dir: str):
    global _cached_model, _cached_path
    with _model_lock:
        if _cached_path != model_path:
            import mindspore
            from mindnlp.transformers import AutoModelForCausalLM, AutoTokenizer

            dtype_name = os.environ.get("MINDPILOT_LOCAL_DTYPE", "float16")
            if dtype_name not in ("float16", "float32", "bfloat16"):
                raise ValueError("MINDPILOT_LOCAL_DTYPE 必须为 float16、float32 或 bfloat16")
            device = os.environ.get("MINDPILOT_LOCAL_DEVICE")
            if device:
                mindspore.set_context(device_target=device)
            _cached_model = None
            _cached_path = None
            tokenizer = AutoTokenizer.from_pretrained(model_path, cache_dir=cache_dir)
            model = AutoModelForCausalLM.from_pretrained(
                model_path, ms_dtype=getattr(mindspore, dtype_name), cache_dir=cache_dir
            )
            model.set_train(False)
            _cached_model = (tokenizer, model)
            _cached_path = model_path
        return _cached_model


class LocalChatModel(BaseChatModel):
    model_name: str
    cache_dir: str
    temperature: float = 0.8
    max_tokens: int = 4096

    @property
    def _llm_type(self) -> str:
        return "mindnlp-local"

    @property
    def _identifying_params(self) -> dict:
        return {"model_name": self.model_name}

    def _generate(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None,
        run_manager=None, **kwargs: Any,
    ) -> ChatResult:
        model_path = resolve_model_path(self.model_name)
        options = generation_options(self.temperature, self.max_tokens)
        roles = {"human": "user", "ai": "assistant", "system": "system"}
        conversation = []
        for message in messages:
            if message.type not in roles or not isinstance(message.content, str):
                raise ValueError("本地模型只接受文本形式的 system、user、assistant 消息")
            conversation.append({"role": roles[message.type], "content": message.content})

        # 模型切换和生成共用锁，限制显存占用并防止并发修改生成状态。
        with _model_lock:
            tokenizer, model = load_local_model(model_path, self.cache_dir)
            prompt = tokenizer.apply_chat_template(
                conversation, tokenize=False, add_generation_prompt=True
            )
            inputs = tokenizer(prompt, return_tensors="ms")
            outputs = model.generate(**inputs, **options)
            generated = outputs[0][inputs["input_ids"].shape[-1]:]
            text = tokenizer.decode(generated, skip_special_tokens=True)
        return ChatResult(generations=[ChatGeneration(
            message=AIMessage(content=truncate_at_stop(text, stop))
        )])
