#!/bin/bash

# Set up a local folder structure for end-to-end testing of the stignore-agent with a stignore-manager

AGENT_HOST="${1:-0.0.0.0}"
AGENT_PORT="${2:-8080}"

TEST_ID=$(od -A n -t d -N 1 /dev/urandom |tr -d ' \n')

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Setup test data directory
TEST_DIR="${SCRIPT_DIR}/test_${TEST_ID}"

mkdir -p "${TEST_DIR}"

${SCRIPT_DIR}/generate_test_data.py "${TEST_DIR}"

# Build the docker image and run the agent
cd ${SCRIPT_DIR}/..

docker build -t stignore-agent:local -f Dockerfile-dev .

docker run -it --rm --name "stignore-agent-${TEST_ID}" -p "${AGENT_PORT}:${AGENT_PORT}/tcp" -v "${TEST_DIR}:${TEST_DIR}" stignore-agent:local --host "${AGENT_HOST}" --port "${AGENT_PORT}" --config-file "${TEST_DIR}/config.yml"

# Clean up after ourselves
rm -rf "${TEST_DIR}"
