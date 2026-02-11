#!/bin/bash
mkdir -p ~/.streamlit/

cat <<EOF > ~/.streamlit/config.toml
[server]
headless = true
port = ${PORT:-8501}
enableCORS = false
EOF
