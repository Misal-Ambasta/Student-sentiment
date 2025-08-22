# Frontend API Changes Summary

## Overview
This document summarizes the changes made to the frontend to align with the updated backend `/api/chat/query` endpoint.

## Changes Made

### 1. Updated API Types (`src/lib/api.ts`)

#### ChatRequest Interface
**Before:**
```typescript
export interface ChatRequest {
  query: string;
  session_id?: string;
  classification?: string;
  context?: Record<string, any>;
  response_format?: 'conversational' | 'weekly_report' | 'individual_analysis' | 'segmentation_analysis' | 'aspect_specific';
  filters?: Record<string, any>;
}
```

**After:**
```typescript
export interface ChatRequest {
  query: string;
  session_id?: string;
  response_format?: string;
  auto_classify?: string; // "true" or "false" as string
  student_id?: string;
  course_id?: string;
}
```

#### ChatResponse Interface
**Before:**
```typescript
export interface ChatResponse {
  response: string;
  query_type: string;
  sources: Array<{
    collection: string;
    relevance_score: number;
    metadata: Record<string, any>;
  }>;
  analysis_metadata: Record<string, any>;
  response_format: string;
  timestamp: string;
  confidence?: number;
  suggestions?: string[];
}
```

**After:**
```typescript
export interface ChatResponse {
  session_id: string;
  query: string;
  response: string | object; // Can be string or parsed JSON object for structured responses
  classification: string;
  analysis_type?: string | null;
}
```

### 2. Updated Chat Component (`src/pages/Chat.tsx`)

#### Request Parameters
**Before:**
```typescript
const response = await sendChatMessage({
  query: userMessage,
  session_id: currentSession?.id,
  classification: classification.query_type
});
```

**After:**
```typescript
const response = await sendChatMessage({
  query: userMessage,
  session_id: currentSession?.id,
  response_format: classification.query_type,
  auto_classify: "false"
});
```

#### Response Handling
**Before:**
```typescript
const assistantMsg = {
  content: response.response,
  type: 'assistant' as const,
  sources: response.sources,
  queryType: response.query_type,
  analysisMetadata: response.analysis_metadata,
  responseFormat: response.response_format
};
```

**After:**
```typescript
const assistantMsg = {
  content: typeof response.response === 'string' ? response.response : JSON.stringify(response.response, null, 2),
  type: 'assistant' as const,
  queryType: response.classification,
  analysisType: response.analysis_type
};
```

### 3. Updated Chat Store (`src/stores/useChatStore.ts`)

#### ChatMessage Interface
**Before:**
```typescript
export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  queryType?: string;
  sources?: ChatResponse['sources'];
  analysisMetadata?: Record<string, any>;
  responseFormat?: string;
  isStreaming?: boolean;
  error?: string;
}
```

**After:**
```typescript
export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  queryType?: string;
  analysisType?: string | null;
  isStreaming?: boolean;
  error?: string;
}
```

### 4. Updated Message Display

#### Removed Features
- Sources display (no longer provided by backend)
- Confidence score display (no longer provided by backend)
- Suggestions handling (no longer provided by backend)

#### Added Features
- Query Type badge display
- Analysis Type badge display (when available)
- Support for structured JSON responses (formatted as readable text)

## Key Differences from Backend

### Backend Response Structure
```json
{
  "session_id": "uuid",
  "query": "user query",
  "response": "assistant response or JSON object",
  "classification": "query_type",
  "analysis_type": "type or null"
}
```

### Frontend Expectations
The frontend now correctly expects:
- `session_id` instead of generating its own
- `classification` field containing the query type
- `analysis_type` field for structured analysis responses
- `response` field that can be either string or object
- No `sources`, `confidence`, or `suggestions` fields

## Testing

A test script has been created at `test_frontend_api_integration.js` to verify the integration works correctly. Run this in the browser console to test:

1. Manual classification requests
2. Auto-classification requests  
3. Classification endpoint functionality

## Migration Notes

### For Developers
1. Update any components using the old `ChatResponse` interface
2. Remove references to `sources`, `confidence`, and `suggestions`
3. Use `classification` instead of `query_type` for the response classification
4. Handle both string and object responses in the `response` field
5. Use `auto_classify` parameter as string ("true"/"false") not boolean

### Backward Compatibility
These changes are **breaking changes** and are not backward compatible with the old API structure. All frontend components using the chat API must be updated.

## Status
✅ **Complete** - All frontend components have been updated to work with the new backend API structure.