#!/usr/bin/env bash
# Re-creates repos/ and luca_repos/ at the exact commits used in the thesis.
# Usage: bash clone_repos.sh [target-dir]   (default: current directory)
set -e; T="${1:-.}"
clone(){ local path="$1" url="$2" sha="$3"; mkdir -p "$T/$(dirname "$path")"; if [ ! -d "$T/$path/.git" ]; then git clone -q "$url" "$T/$path"; fi; git -C "$T/$path" fetch -q origin "$sha" 2>/dev/null || git -C "$T/$path" fetch -q origin; git -C "$T/$path" checkout -q "$sha"; echo "ok $path @ ${sha:0:10}"; }
clone "repos/godot" "https://github.com/godotengine/godot.git" "bbe965432747f49ac647883c871a38ade26bdc4a"
clone "repos/grafana" "https://github.com/grafana/grafana.git" "24e4e0946dd14a4e51ffd6489c00390648c2377e"
clone "repos/jenkins" "https://github.com/jenkinsci/jenkins.git" "e5dd70c57ba6b814971752919a368ad8787a6c61"
clone "repos/kafka" "https://github.com/apache/kafka.git" "68800a027b70ab9a34a79aa779a1eefcbbba684c"
clone "luca_repos/apache_kafka" "https://github.com/apache/kafka.git" "11688f2129ef7eb1c541d93a19cc05d1fc6058d0"
clone "luca_repos/django_django" "https://github.com/django/django.git" "2831eaed797627e6e6410b06f74dadeb63316e09"
clone "luca_repos/godotengine_godot" "https://github.com/godotengine/godot.git" "bbe965432747f49ac647883c871a38ade26bdc4a"
clone "luca_repos/grafana_grafana" "https://github.com/grafana/grafana.git" "4669da5c69e5cbe4a358c19cce3be604cc970518"
clone "luca_repos/jenkinsci_jenkins" "https://github.com/jenkinsci/jenkins.git" "471a287b57072d96853eb0c86b68093ad3c47a19"
clone "luca_repos/microsoft_TypeScript" "https://github.com/microsoft/TypeScript.git" "d9d9eeafa0a2bb1fd327b3af15edacade7544e5f"
clone "luca_repos/scikit-learn_scikit-learn" "https://github.com/scikit-learn/scikit-learn.git" "b0bf5d7280e8768e3add0d9c83ae950436a1b878"
