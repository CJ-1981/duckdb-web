/**
 * Shared AI provider and model configuration for all AI builders.
 *
 * This configuration is used by:
 * - AiSqlBuilderPanel (natural language to SQL)
 * - AiPipelineBuilderPanel (natural language to workflow JSON)
 *
 * To add a custom model at runtime, users can select "Custom" and enter
 * any model ID that's compatible with the selected provider's API.
 */

export interface Provider {
  id: string;
  name: string;
  baseUrl: string;
  type: 'openai' | 'anthropic' | 'google';
  apiKeyUrl: string;
  extraHeaders?: Record<string, string>;
  models: { id: string; name: string }[];
}

export const CUSTOM_MODEL_OPTION = {
  id: '__custom__',
  name: 'Custom (enter model ID)',
};

/**
 * Complete provider list with all supported models.
 *
 * Each provider includes their full model catalog. Users can also
 * select "Custom" to enter any model ID manually (useful for new
 * models or private deployments).
 */
export const PROVIDERS: Provider[] = [
  {
    id: 'google',
    name: 'Google (Gemini)',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta/models',
    type: 'google',
    apiKeyUrl: 'https://aistudio.google.com/app/apikey',
    models: [
      // Gemini 2.5 Series (Latest Stable)
      { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash' },
      { id: 'gemini-2.5-flash-lite', name: 'Gemini 2.5 Flash Lite' },
      { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro' },
      { id: 'gemini-2.5-flash-exp', name: 'Gemini 2.5 Flash (Experimental)' },
      { id: 'gemini-2.5-pro-exp', name: 'Gemini 2.5 Pro (Experimental)' },
      // Gemini 2.0 Series
      { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash' },
      { id: 'gemini-2.0-flash-exp', name: 'Gemini 2.0 Flash (Experimental)' },
      { id: 'gemini-2.0-flash-thinking', name: 'Gemini 2.0 Flash Thinking' },
      { id: 'gemini-2.0-flash-thinking-exp', name: 'Gemini 2.0 Flash Thinking (Experimental)' },
      { id: 'gemini-2.0-pro', name: 'Gemini 2.0 Pro' },
      { id: 'gemini-2.0-pro-exp', name: 'Gemini 2.0 Pro (Experimental)' },
      // Gemini 1.5 Series
      { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash' },
      { id: 'gemini-1.5-flash-8b', name: 'Gemini 1.5 Flash (8B)' },
      { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro' },
      { id: 'gemini-1.5-pro-8b', name: 'Gemini 1.5 Pro (8B)' },
      // Gemini 1.0 Series (Legacy)
      { id: 'gemini-1.0-pro', name: 'Gemini 1.0 Pro' },
      { id: 'gemini-1.0-pro-001', name: 'Gemini 1.0 Pro (001)' },
      // Gemini 3.0 Preview (Cutting Edge)
      { id: 'gemini-3-flash-preview', name: 'Gemini 3.0 Flash (Preview)' },
      { id: 'gemini-3-flash-preview-exp', name: 'Gemini 3.0 Flash (Experimental)' },
      { id: 'gemini-3.1-flash-lite-preview', name: 'Gemini 3.1 Flash Lite (Preview)' },
      { id: 'gemini-exp-1206', name: 'Gemini Experimental (1206)' },
    ],
  },
  {
    id: 'groq',
    name: 'Groq',
    baseUrl: 'https://api.groq.com/openai/v1/chat/completions',
    type: 'openai',
    apiKeyUrl: 'https://console.groq.com/keys',
    models: [
      // Llama 3.3 Series
      { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B Versatile' },
      // Llama 3.1 Series
      { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B Instant' },
      { id: 'llama-3.1-70b-versatile', name: 'Llama 3.1 70B Versatile' },
      // Mixtral
      { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B 32K' },
      // Gemma
      { id: 'gemma2-9b-it', name: 'Gemma 2 9B' },
      { id: 'gemma-7b-it', name: 'Gemma 7B' },
      // Qwen
      { id: 'qwen-2.5-72b-instruct', name: 'Qwen 2.5 72B' },
    ],
  },
  {
    id: 'cerebras',
    name: 'Cerebras',
    baseUrl: 'https://api.cerebras.ai/v1/chat/completions',
    type: 'openai',
    apiKeyUrl: 'https://cloud.cerebras.ai/',
    models: [
      // Llama 3.3 Series
      { id: 'llama-3.3-70b', name: 'Llama 3.3 70B' },
      // Llama 3.1 Series
      { id: 'llama3.1-8b', name: 'Llama 3.1 8B' },
      { id: 'llama-3.1-70b', name: 'Llama 3.1 70B' },
      // Llama 3 Series
      { id: 'llama-3-8b', name: 'Llama 3 8B' },
      { id: 'llama-3-70b', name: 'Llama 3 70B' },
      // Mixtral
      { id: 'mixtral-8x7b', name: 'Mixtral 8x7B' },
    ],
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    baseUrl: 'https://openrouter.ai/api/v1/chat/completions',
    type: 'openai',
    apiKeyUrl: 'https://openrouter.ai/keys',
    extraHeaders: {
      'HTTP-Referer': 'https://duckdb-platform.local',
      'X-Title': 'DuckDB AI Builders'
    },
    models: [
      // Anthropic
      { id: 'anthropic/claude-3.5-sonnet', name: 'Claude 3.5 Sonnet' },
      { id: 'anthropic/claude-3.5-haiku', name: 'Claude 3.5 Haiku' },
      { id: 'anthropic/claude-3-opus', name: 'Claude 3 Opus' },
      // OpenAI
      { id: 'openai/gpt-4o', name: 'GPT-4o' },
      { id: 'openai/gpt-4o-mini', name: 'GPT-4o mini' },
      { id: 'openai/o1-mini', name: 'o1-mini' },
      { id: 'openai/o1-preview', name: 'o1-preview' },
      // Meta
      { id: 'meta-llama/llama-3.3-70b-instruct', name: 'Llama 3.3 70B' },
      { id: 'meta-llama/llama-3.1-405b-instruct', name: 'Llama 3.1 405B' },
      { id: 'meta-llama/llama-3.1-70b-instruct', name: 'Llama 3.1 70B' },
      { id: 'meta-llama/llama-3.1-8b-instruct', name: 'Llama 3.1 8B' },
      // Google Gemini (Latest)
      { id: 'google/gemini-2.5-flash', name: 'Gemini 2.5 Flash' },
      { id: 'google/gemini-2.5-flash-lite', name: 'Gemini 2.5 Flash Lite' },
      { id: 'google/gemini-2.5-pro', name: 'Gemini 2.5 Pro' },
      { id: 'google/gemini-2.0-flash', name: 'Gemini 2.0 Flash' },
      { id: 'google/gemini-2.0-flash-thinking', name: 'Gemini 2.0 Flash Thinking' },
      { id: 'google/gemini-2.0-pro', name: 'Gemini 2.0 Pro' },
      { id: 'google/gemini-1.5-flash', name: 'Gemini 1.5 Flash' },
      { id: 'google/gemini-1.5-pro', name: 'Gemini 1.5 Pro' },
      { id: 'google/gemini-flash-1.5', name: 'Gemini 1.5 Flash (Legacy)' },
      { id: 'google/gemini-pro-1.5', name: 'Gemini 1.5 Pro (Legacy)' },
      { id: 'google/gemini-3-flash-preview', name: 'Gemini 3.0 Flash (Preview)' },
      { id: 'google/gemini-3.1-flash-lite-preview', name: 'Gemini 3.1 Flash Lite (Preview)' },
      // DeepSeek
      { id: 'deepseek/deepseek-chat', name: 'DeepSeek Chat' },
      { id: 'deepseek/deepseek-chat:latest', name: 'DeepSeek Chat (Latest)' },
      { id: 'deepseek/deepseek-r1', name: 'DeepSeek R1' },
      // Mistral
      { id: 'mistralai/mistral-large', name: 'Mistral Large' },
      { id: 'mistralai/mistral-small', name: 'Mistral Small' },
      { id: 'mistralai/ministral-3b', name: 'Ministral 3B' },
      // Qwen
      { id: 'qwen/qwen-2.5-72b-instruct', name: 'Qwen 2.5 72B' },
      { id: 'qwen/qwen-2-72b-instruct', name: 'Qwen 2 72B' },
      { id: 'qwen/qwen-2.5-coder-32b-instruct', name: 'Qwen 2.5 Coder 32B' },
    ],
  },
  {
    id: 'openai',
    name: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1/chat/completions',
    type: 'openai',
    apiKeyUrl: 'https://platform.openai.com/api-keys',
    models: [
      // GPT-4o Series
      { id: 'gpt-4o', name: 'GPT-4o' },
      { id: 'gpt-4o-mini', name: 'GPT-4o mini' },
      // O1 Series (Reasoning Models)
      { id: 'o1-mini', name: 'o1-mini' },
      { id: 'o1-preview', name: 'o1-preview' },
      // GPT-4 Turbo (Legacy)
      { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
      { id: 'gpt-4-turbo-preview', name: 'GPT-4 Turbo Preview' },
    ],
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    baseUrl: 'https://api.anthropic.com/v1/messages',
    type: 'anthropic',
    apiKeyUrl: 'https://console.anthropic.com/settings/keys',
    models: [
      // Claude 3.5 Series (Latest)
      { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet' },
      { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku' },
      // Claude 3 Series (Previous)
      { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus' },
      { id: 'claude-3-sonnet-20240229', name: 'Claude 3 Sonnet' },
      { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku' },
    ],
  },
];
