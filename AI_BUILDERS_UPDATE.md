# AI Builders Model Consistency Update

## Summary

Made AI SQL Builder and AI Pipeline Builder consistent with models and added a custom model option that allows users to enter any model ID directly.

## Changes

### 1. Created Shared Provider Configuration
- **File**: `src/config/ai-providers.ts`
- Unified all AI provider configurations into a single shared module
- Includes 6 providers: Google (Gemini), Groq, Cerebras, OpenRouter, OpenAI, Anthropic
- Total of 66+ pre-configured models
- Added `CUSTOM_MODEL_OPTION` constant for the custom model dropdown entry

### 2. Updated AiSqlBuilderPanel
- **File**: `src/components/panels/AiSqlBuilderPanel.tsx`
- Removed duplicate provider configuration (157 lines)
- Imported shared configuration from `src/config/ai-providers.ts`
- Added custom model state (`customModelId`)
- Added logic to use custom model ID when "Custom" option is selected
- Added validation for custom model ID input
- Added custom model input field that appears when "Custom" is selected
- Removed unused React import

### 3. Updated AiPipelineBuilderPanel
- **File**: `src/components/panels/AiPipelineBuilderPanel.tsx`
- Removed duplicate provider configuration (39 lines)
- Imported shared configuration from `src/config/ai-providers.ts`
- Added custom model state (`customModelId`)
- Added logic to use custom model ID when "Custom" option is selected
- Added validation for custom model ID input
- Added custom model input field that appears when "Custom" is selected

## Features

### Consistent Model Lists
Both AI builders now have access to the same comprehensive list of providers and models:
- Google (Gemini): 22 models (1.0, 1.5, 2.0, 2.5, 3.0, 3.1 series)
- Groq: 7 models (Llama 3.3/3.1, Mixtral, Gemma, Qwen)
- Cerebras: 6 models (Llama series)
- OpenRouter: 26 models (Claude, GPT, Llama, Gemini, DeepSeek, Mistral, Qwen)
- OpenAI: 5 models (GPT-4o, o1 series)
- Anthropic: 5 models (Claude 3.5, 3 series)

### Custom Model Support
Users can now:
1. Select "Custom (enter model ID)" from the model dropdown
2. Enter any model ID in a text input field
3. Use new or experimental models not yet in the pre-configured list
4. Use private deployment models or custom model variants

The custom model input:
- Appears only when "Custom" is selected
- Shows helpful placeholder text with examples
- Includes provider-specific guidance
- Validates that a model ID is entered before generation

## Benefits

1. **Consistency**: Both builders now show the same providers and models
2. **Flexibility**: Users can use any model ID without waiting for code updates
3. **Maintainability**: Single source of truth for provider configurations
4. **Future-proof**: Easy to add new providers/models in one place
5. **User Experience**: Clear indication of custom model option with helpful hints

## Testing

Build verification:
```bash
npm run build
```

Status: ✓ Compiled successfully

## Usage

When the custom model option is selected:
1. User sees a text input field labeled "Custom Model ID"
2. Placeholder shows example model IDs
3. Help text indicates which provider's documentation to check
4. Validation ensures model ID is not empty before generation

Example custom model IDs users might enter:
- `gemini-2.0-flash-thinking-exp-01-21` (Google Gemini experimental)
- `gpt-4-turbo-2024-04-09` (OpenAI specific version)
- `claude-3-7-sonnet-20250219` (future Claude model)
- `llama-3.3-70b-versatile:beta` (Groq beta model)
