# Requirements Document

## Introduction

A FastAPI backend service that processes audio data stored in a Supabase database, converts speech to text using OpenAI Whisper, and calculates vector similarity between the transcribed text and reference documents using OpenAI embeddings.

## Glossary

- **Speech_Similarity_API**: The FastAPI backend service that handles speech-to-text conversion and similarity analysis
- **Supabase_Database**: PostgreSQL database accessed via Supabase connection pooler containing session data
- **OpenAI_Whisper**: OpenAI's speech-to-text transcription service
- **OpenAI_Embeddings**: OpenAI's text embedding model for vector representation
- **Session_Record**: Database row in sessions table identified by session ID
- **Audio_Data**: Base64-encoded WAV mono audio file stored in database
- **Vector_Similarity**: Cosine similarity calculation between text embeddings
- **Original_Paper**: Reference text document used for similarity comparison

## Requirements

### Requirement 1

**User Story:** As an API client, I want to submit a session ID and receive a similarity score between the session's audio transcription and a reference document, so that I can analyze content relevance.

#### Acceptance Criteria

1. WHEN a valid session ID is provided via API endpoint, THE Speech_Similarity_API SHALL retrieve the corresponding Session_Record from Supabase_Database
2. THE Speech_Similarity_API SHALL decode the Audio_Data from base64 format and convert it to a processable audio format
3. THE Speech_Similarity_API SHALL transcribe the audio using OpenAI_Whisper service
4. THE Speech_Similarity_API SHALL generate embeddings for both the transcribed text and Original_Paper using OpenAI_Embeddings
5. THE Speech_Similarity_API SHALL calculate Vector_Similarity between the two embeddings and return the similarity score

### Requirement 2

**User Story:** As a system administrator, I want the API to handle errors gracefully with appropriate HTTP status codes, so that clients can understand and respond to different failure scenarios.

#### Acceptance Criteria

1. WHEN an invalid session ID is provided, THE Speech_Similarity_API SHALL return HTTP 404 status with descriptive error message
2. WHEN Supabase_Database connection fails, THE Speech_Similarity_API SHALL return HTTP 503 status with service unavailable message
3. WHEN OpenAI_Whisper service is unavailable, THE Speech_Similarity_API SHALL return HTTP 502 status with external service error message
4. WHEN Audio_Data is corrupted or invalid, THE Speech_Similarity_API SHALL return HTTP 422 status with validation error message
5. IF any unexpected error occurs, THEN THE Speech_Similarity_API SHALL return HTTP 500 status with generic error message

### Requirement 3

**User Story:** As a security-conscious developer, I want sensitive credentials to be stored securely in environment variables, so that API keys and database connections are protected.

#### Acceptance Criteria

1. THE Speech_Similarity_API SHALL load OpenAI API credentials from environment variables
2. THE Speech_Similarity_API SHALL load Supabase connection string from environment variables
3. THE Speech_Similarity_API SHALL validate that all required environment variables are present at startup
4. THE Speech_Similarity_API SHALL not expose credentials in logs or error messages
5. THE Speech_Similarity_API SHALL use secure connection protocols for all external service communications

### Requirement 4

**User Story:** As an API client, I want to receive structured JSON responses with consistent formatting, so that I can reliably parse and use the API results.

#### Acceptance Criteria

1. THE Speech_Similarity_API SHALL return similarity scores as floating-point numbers between 0 and 1
2. THE Speech_Similarity_API SHALL include all Session_Record fields (id, speech, questions, created_by, generated_by, created_at, audio) in the response payload
3. THE Speech_Similarity_API SHALL include the transcribed text in the response payload
4. THE Speech_Similarity_API SHALL provide response timestamps for audit purposes
5. THE Speech_Similarity_API SHALL follow consistent JSON schema for all endpoint responses

### Requirement 5

**User Story:** As an API client, I want to update the audio data for an existing session, so that I can replace or correct audio recordings without creating new sessions.

#### Acceptance Criteria

1. WHEN a valid session ID and base64 audio data are provided via PUT endpoint, THE Speech_Similarity_API SHALL update the Audio_Data field in the corresponding Session_Record
2. THE Speech_Similarity_API SHALL validate the audio format and encoding before updating
3. WHEN the session ID does not exist, THE Speech_Similarity_API SHALL return HTTP 404 status
4. WHEN the audio update is successful, THE Speech_Similarity_API SHALL return HTTP 200 status with confirmation message
5. THE Speech_Similarity_API SHALL preserve all other Session_Record fields during audio updates

### Requirement 6

**User Story:** As a developer, I want the API to follow FastAPI best practices with proper validation and documentation, so that the service is maintainable and well-documented.

#### Acceptance Criteria

1. THE Speech_Similarity_API SHALL use Pydantic models for request and response validation
2. THE Speech_Similarity_API SHALL generate OpenAPI documentation automatically
3. THE Speech_Similarity_API SHALL implement proper dependency injection for database and external service connections
4. THE Speech_Similarity_API SHALL use structured logging for monitoring and debugging
5. THE Speech_Similarity_API SHALL implement health check endpoints for service monitoring