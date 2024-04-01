#!/usr/bin/env bash

help() {
  cat 1>&2 <<EOF
Builds and runs a Python Streamlit Application using Docker
USAGE:
    run_ui [OPTIONS]
OPTIONS:
    -t, --type <deploy-type> Deployment type you want to run.
    -k, --key  <API-KEY>     OpenAI API Key
EOF
  echo "Usage:"
  echo "./run_ui.sh"
}

parse_opts() {
  while test $# -gt 0; do
    key="$1"
    case "$key" in
    -t | --type)
      DEPLOY_TYPE="$2"
      shift
      ;;
    -k | --key)
      OPEN_API_KEY="$2"
      shift
      ;;
    -h | --help)
      help
      exit 0
      ;;
    *)
      help
      ;;
    esac
    shift
  done
}

function is_empty {
  if [ -z "$1" ]; then
      return
  else
      false
  fi
}

function docker_running {
  docker_state=$(docker info >/dev/null 2>&1)
  if [[ $? -ne 0 ]]; then
    false
  else
    true
  fi
}

# Replace with your organization/personal API Key Secret
# Or provide it as a command line argument using -k or --key
OPEN_API_SECRET="SECRET-HERE-OR-PROVIDE-IN-COMMAND-LINE-ARGS"

create_dockerfile() {
  # Replace placeholder values into a Dockerfile
  sed -e "s/\${i}/1/" -e "s/\${OPENAI_API_KEY}/"$OPEN_API_SECRET"/" dockerfile_tmp > dockerfile_local
}

build_docker_image() {
  # Note, this can take a bit of time to build so go get a coffee
  echo "Building Docker Image"
  docker build -t nfl-streamlit -f dockerfile_local .
}

run_docker_streamlit() {
  echo "Running Docker Image"
  docker run -p 80:80 nfl-streamlit
}

main() {
  parse_opts "$@"
  DEPLOY_TYPE=${DEPLOY_TYPE:-'ALL'}

  # Check if Docker is running. If it isn't then terminate the script
  if ! docker_running; then
    echo "Please start Docker before you execute this script!"
    exit 1
  fi

  # Check and set API Key as needed
  if is_empty $OPEN_API_KEY; then
    echo "No OpenAI API Key Provided! Make sure this is set in the bash script before building the Docker image."
  else
    echo "OpenAI Key Provided!"
    OPEN_API_SECRET="$OPEN_API_KEY"
  fi

  # Examine deployment type and execute the necessary operations
  if [ "$DEPLOY_TYPE" = 'BUILD' ]; then
    create_dockerfile
    build_docker_image
  elif [ "$DEPLOY_TYPE" = 'RUN_LOCAL' ]; then
    run_docker_streamlit
  elif [ "$DEPLOY_TYPE" = 'ALL' ]; then
    create_dockerfile
    build_docker_image
    run_docker_streamlit
  else
    echo "Invalid Deployment Options"
    exit 1
  fi
}

main "$@" || exit 1