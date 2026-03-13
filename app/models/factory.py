class ModelFactory:
    @staticmethod
    def create_model(model_name, *args, provider=None):
        """
        Create a model instance based on provider and/or model name.

        args: (base_url, api_key, context, screen)

        When *provider* is set, it takes priority over model-name-based
        routing.  This enables OpenRouter, Ollama, and Claude support.
        """
        try:
            # ── Provider-based routing (new) ──
            if provider == 'Claude':
                from models.claude import Claude
                return Claude(model_name, *args[1:])

            if provider in ('OpenRouter', 'Ollama'):
                from models.chat_completions import ChatCompletionsModel
                return ChatCompletionsModel(model_name, *args)

            if provider == 'Gemini':
                from models.gemini import Gemini
                return Gemini(model_name, *args[1:])

            # ── Model-name-based routing (backward compat) ──
            if model_name == 'moondream2':
                from models.moondream_hybrid import MoondreamHybrid
                return MoondreamHybrid(model_name, *args)
            elif model_name == 'gpt-4o' or model_name == 'gpt-4o-mini':
                from models.gpt4o import GPT4o
                return GPT4o(model_name, *args)
            elif model_name == 'computer-use-preview':
                from models.openai_computer_use import OpenAIComputerUse
                return OpenAIComputerUse(model_name, *args)
            elif model_name.startswith('gpt-5'):
                from models.gpt5 import GPT5
                return GPT5(model_name, *args)
            elif model_name == 'gpt-4-vision-preview' or model_name == 'gpt-4-turbo':
                from models.gpt4v import GPT4v
                return GPT4v(model_name, *args)
            elif model_name.startswith("gemini"):
                from models.gemini import Gemini
                return Gemini(model_name, *args[1:])
            else:
                from models.gpt4v import GPT4v
                return GPT4v(model_name, *args)
        except Exception as e:
            raise ValueError(f'Unsupported model type {model_name}. Create entry in app/models/. Error: {e}')
