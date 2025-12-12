#!/bin/bash

retry_command() {
  local max_attempts=8
  local timeout=5
  local attempt=1
  local exit_code=0

  while [ $attempt -le $max_attempts ]; do
    "$@"
    exit_code=$?

    if [ $exit_code -eq 0 ]; then
      break
    fi

    echo "Attempt $attempt failed! Retrying in $timeout seconds..."
    sleep $timeout
    attempt=$((attempt + 1))
    timeout=$((timeout * 2))
  done

  if [ $exit_code -ne 0 ]; then
    echo "Command $@ failed after $attempt attempts!"
  fi

  return $exit_code
}
export -f retry_command

retry_command_lin() {
  local max_attempts=256
  local timeout=2
  local attempt=1
  local exit_code=0

  while [ $attempt -le $max_attempts ]; do
    "$@"
    exit_code=$?

    if [ $exit_code -eq 0 ]; then
      break
    fi

    echo "Attempt $attempt failed! Retrying in $timeout seconds..."
    sleep $timeout
    attempt=$((attempt + 1))
  done

  if [ $exit_code -ne 0 ]; then
    echo "Command $@ failed after $attempt attempts!"
  fi

  return $exit_code
}
export -f retry_command_lin

check_es_health() {
  # Use ELASTIC_ENDPOINT from environment (set after sourcing .env)
  local es_url="${ELASTIC_ENDPOINT:-http://kubernetes-vm:30920}"

  output=$(curl -s -X POST "$es_url/test/_doc" \
    -H 'Content-Type: application/json' \
    -H "$AUTH_HEADER" \
    -d '{"message": "Hello World"}')
  echo $output
  RESULT=$(echo $output | jq -r '.result')
  if [[ $RESULT = created ]]; then
    echo "check_es_health: doc created"
  else
    echo "Waiting for Elasticsearch: $output"
    return 1
  fi

  output=$(curl -s -X GET "$es_url/test/_search" \
    -H 'Content-Type: application/json' \
    -H "$AUTH_HEADER")
  RESULT=$(echo $output | jq -r '._shards.successful')
  if [[ $RESULT = 1 ]]; then
    echo "check_es_health: doc searched"
  else
    echo "Waiting for Elasticsearch: $output"
    return 1
  fi

  output=$(curl -s -X DELETE "$es_url/test" \
    -H 'Content-Type: application/json' \
    -H "$AUTH_HEADER")
  RESULT=$(echo $output | jq -r '.acknowledged')
  if [[ $RESULT = true ]]; then
    echo "check_es_health: index deleted"
  else
    echo "Waiting for Elasticsearch: $output"
    return 1
  fi
}
export -f check_es_health

# =============================================================================
# Configuration - Load from environment or .env file
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

# Load .env file if it exists
if [[ -f "$ENV_FILE" ]]; then
    echo "Loading environment from: $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
fi

# Kibana URL - use KIBANA_URL from environment, default to ECK NodePort
KIBANA_URL_LOCAL="${KIBANA_URL:-http://kubernetes-vm:30002}"

# Authentication - prefer API key, fall back to basic auth
if [[ -n "${ELASTIC_API_KEY:-}" ]]; then
    AUTH_HEADER="Authorization: ApiKey ${ELASTIC_API_KEY}"
else
    # Fallback to basic auth (elastic:elastic)
    ELASTICSEARCH_AUTH_BASE64="ZWxhc3RpYzplbGFzdGlj"
    AUTH_HEADER="Authorization: Basic ${ELASTICSEARCH_AUTH_BASE64}"
fi

# LLM Configuration - use environment variables directly
# These should be set as LLM_PROXY_URL and LLM_APIKEY in the environment
echo "LLM_PROXY_URL=${LLM_PROXY_URL:-not set}"
echo "LLM_APIKEY=${LLM_APIKEY:+[set]}"
echo "KIBANA_URL_LOCAL=${KIBANA_URL_LOCAL}"

# Elastic Stack Version
ELASTIC_STACK_VERSION=9.0.0

model=gpt-4o
connector=true
knowledgebase=true
docs=false
everywhere=true
prompt=false
while getopts "m:k:c:p:d:e:" opt; do
  case "$opt" in
  c) connector="$OPTARG" ;;
  m) model="$OPTARG" ;;
  k) knowledgebase="$OPTARG" ;;
  d) docs="$OPTARG" ;;
  e) everywhere="$OPTARG" ;;
  p) prompt="$OPTARG" ;;
  esac
done
echo "model=$model"
echo "knowledgebase=$knowledgebase"
echo "docs=$docs"
echo "everywhere=$everywhere"
echo "prompt=$prompt"

####################################################################### OPENAI
# Install LLM in ES

if [ "$connector" = true ]; then
  echo "Adding LLM connector"
  add_connector() {
    local http_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$KIBANA_URL_LOCAL/api/actions/connector" \
      -H 'Content-Type: application/json' \
      -H "kbn-xsrf: true" \
      -H "$AUTH_HEADER" \
      -H "x-elastic-internal-origin: Kibana" \
      -d '{
    "name":"openai-connector",
    "config": {
        "apiProvider":"OpenAI",
        "apiUrl":"https://'"$LLM_PROXY_URL"'/v1/chat/completions",
        "defaultModel": "'"$model"'"
    },
    "secrets": {
        "apiKey": "'"$LLM_APIKEY"'"
    },
    "connector_type_id":".gen-ai"
    }')

    if echo $http_status | grep -q '^2'; then
      echo "Connector added successfully with HTTP status: $http_status"
      return 0
    else
      echo "Failed to add connector. HTTP status: $http_status"
      return 1
    fi
  }
  retry_command_lin add_connector
fi # if [ "$connector" = true ]

if [ "$knowledgebase" = true ]; then
  # init knowledgebase
  echo "Initializing knowledgebase"
  init_kb() {
    local http_status

    if [[ $ELASTIC_STACK_VERSION == 8.* ]]; then
      http_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$KIBANA_URL_LOCAL/internal/observability_ai_assistant/kb/setup" \
        -H 'Content-Type: application/json' \
        -H "kbn-xsrf: true" \
        -H "$AUTH_HEADER" \
        -H 'x-elastic-internal-origin: Kibana')
    elif [[ $ELASTIC_STACK_VERSION == 9.* ]]; then
      http_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$KIBANA_URL_LOCAL/internal/observability_ai_assistant/kb/setup?inference_id=.elser-2-elasticsearch" \
        -H 'Content-Type: application/json' \
        -H "kbn-xsrf: true" \
        -H "$AUTH_HEADER" \
        -H 'x-elastic-internal-origin: Kibana')
    fi

    if [[ $http_status =~ ^2 ]]; then
      echo "Elastic knowledgebase successfully initialized: $http_status"
      return 0
    else
      echo "Failed to initialize Elastic knowledgebase. HTTP status: $http_status"
      return 1
    fi
  }
  retry_command_lin init_kb

  wait_kb() {
    output=$(curl -X GET -s "$KIBANA_URL_LOCAL/internal/observability_ai_assistant/kb/status" \
      -H "$AUTH_HEADER" \
      -H "Content-Type: application/json" \
      -H "kbn-xsrf: true" \
      -H 'x-elastic-internal-origin: Kibana')

    ENABLED=$(echo "$output" | jq -r '.enabled')

    if [[ $ELASTIC_STACK_VERSION == 8.* ]]; then
      READY=$(echo "$output" | jq -r '.ready')
      MODEL_DEPLOYMENT_STATE=$(echo "$output" | jq -r '.model_stats.deployment_state')
      MODEL_ALLOCATION_STATE=$(echo "$output" | jq -r '.model_stats.allocation_state')

    elif [[ $ELASTIC_STACK_VERSION == 9.1.* ]]; then
      KBSTATE=$(echo "$output" | jq -r '.kbState')

    elif [[ $ELASTIC_STACK_VERSION == 9.* ]]; then
      KBSTATE=$(echo "$output" | jq -r '.inferenceModelState')
    fi

    # Echo vars if they are available
    for var in READY ENABLED MODEL_DEPLOYMENT_STATE MODEL_ALLOCATION_STATE KBSTATE; do
      [[ -n "${!var}" && "${!var}" != "null" ]] && echo "$var: ${!var}"
    done

    if [[ $ENABLED == true && $ELASTIC_STACK_VERSION == 8.* && $READY == true && $MODEL_DEPLOYMENT_STATE == "started" && $MODEL_ALLOCATION_STATE == "fully_allocated" ]]; then
      echo "o11y kb is ready on $attempt"
      return 0
    elif [[ $ENABLED == true && $ELASTIC_STACK_VERSION == 9.* && $KBSTATE == "READY" ]]; then
      echo "o11y kb is ready on $attempt"
      return 0
    else
      echo "o11y kb is not ready on attempt $attempt: $output"
      return 1
    fi
  }
  retry_command_lin wait_kb
fi # if [ "$knowledgebase" = true ]

if [ "$docs" = true ]; then
  echo "Initializing Elastic documentation"
  init_documentation() {
    local http_status

    if [[ $ELASTIC_STACK_VERSION == 8.* ]]; then
      http_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$KIBANA_URL_LOCAL/internal/product_doc_base/install" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -H "$AUTH_HEADER" \
        -H "x-elastic-internal-origin: Kibana")

    elif [[ $ELASTIC_STACK_VERSION == 9.* ]]; then
      http_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$KIBANA_URL_LOCAL/internal/product_doc_base/install" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -H "$AUTH_HEADER" \
        -H "x-elastic-internal-origin: Kibana" \
        -d '{"inferenceId":".elser-2-elasticsearch"}')
    fi

    if [[ $http_status =~ ^2 ]]; then
      echo "Elastic documentation successfully initialized: $http_status"
      return 0
    else
      echo "Failed to initialize Elastic documentation. HTTP status: $http_status"
      return 1
    fi
  }
  retry_command_lin init_documentation
fi # if [ "$docs" = true ]

if [ "$everywhere" = true ]; then
  echo "Initializing AI Assistant Everywhere"
  init_ai_everywhere() {
    local http_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$KIBANA_URL_LOCAL/internal/kibana/settings" \
      -H 'Content-Type: application/json' \
      -H "kbn-xsrf: true" \
      -H "$AUTH_HEADER" \
      -H 'x-elastic-internal-origin: Kibana' \
      -d '{"changes":{"aiAssistant:preferredAIAssistantType":"observability"}}')

    if echo $http_status | grep -q '^2'; then
      echo "Elastic AI Assistant Everywhere successfully initialized: $http_status"
      return 0
    else
      echo "Failed to initialize Elastic AI Assistant Everywhere. HTTP status: $http_status"
      return 1
    fi
  }
  retry_command_lin init_ai_everywhere
fi #if [ "$everywhere" = true ]

if [ "$prompt" = true ]; then
  curl -X PUT "$KIBANA_URL_LOCAL/internal/observability_ai_assistant/kb/user_instructions" \
    -H 'Content-Type: application/json' \
    -H "kbn-xsrf: true" \
    -H "$AUTH_HEADER" \
    -H 'x-elastic-internal-origin: Kibana' \
    -d @./elastic-llm-prompt.json
fi #if [ "$prompt" = true ]